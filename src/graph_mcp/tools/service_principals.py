"""Service principal credential tool (PRD-21618).

graph_service_principal_create_and_add_password mints a short-lived app-only
password credential for an application's service principal, so an MFA push
can be triggered using that app's own identity (the Rewst gap-register flow
this ticket migrates: "[ROC] M365: Push MFA Notification to User"). It is a
three-step composite over Graph's existing /servicePrincipals endpoints:
find-or-create the service principal, then addPassword.

Find-or-create is idempotent (same app_id always resolves to the same
service principal); addPassword is not -- every call mints a brand-new
credential and does not invalidate prior ones, the same non-idempotent
shape users.py's graph_create_tap already ships. Unlike TAP, there is no
removal tool here (Non-goals, docs/tickets/PRD-21618.md) -- repeated calls
accumulate passwordCredentials entries, mitigated in practice by the
short default lifetime, not by cleanup.
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped, error_envelope
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN, odata_quote

_DEFAULT_DISPLAY_NAME = "MSPbots MCP - Temporary Password"
_DEFAULT_LIFETIME_MINUTES = 10


def _format_graph_datetime(value: datetime) -> str:
    """Render a tz-aware datetime the way Graph's own DateTimeOffset fields
    come back (seconds precision, trailing Z), matching the style already
    used for employeeHireDate normalization (users.py's _normalize_hire_date)."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_graph_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
    async def graph_service_principal_create_and_add_password(
        app_id: Annotated[
            str, Field(description="Target application's Application (Client) ID (GUID).")
        ],
        display_name: Annotated[
            str | None,
            Field(
                description=(
                    "Friendly name for the password credential. Defaults to "
                    '"MSPbots MCP - Temporary Password" if omitted.'
                )
            ),
        ] = None,
        start_date_time: Annotated[
            str | None,
            Field(
                description=(
                    "ISO 8601 date-time the credential becomes valid from. Omit "
                    "to make it valid immediately."
                )
            ),
        ] = None,
        lifetime_minutes: Annotated[
            int,
            Field(
                description=(
                    "Minutes from start_date_time (or now) until the credential "
                    "expires. Default 10, matching the MFA-push use case."
                )
            ),
        ] = _DEFAULT_LIFETIME_MINUTES,
    ) -> str:
        """Find or create the service principal for app_id, then add it a
        short-lived password credential so it can authenticate as itself
        (e.g. to trigger an MFA push as an app identity).

        Reuses the existing service principal if one is already registered
        for app_id (created=false); otherwise creates one (created=true).
        Adding the password is not idempotent -- calling again adds another
        credential rather than replacing the last one, and this tool never
        removes credentials it created. secret_text is a one-time secret
        only returned at creation; capture it now, it cannot be read back
        later. Needs Application.ReadWrite.All; 403 until the tenant has
        re-consented after that scope is granted (see README).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        try:
            found = await client.get(
                "/servicePrincipals",
                params={
                    "$filter": f"appId eq '{odata_quote(app_id)}'",
                    "$select": "id,appId",
                },
            )
            matches = found.get("value", []) if isinstance(found, dict) else []

            if len(matches) > 1:
                return error_envelope(
                    "service_principal_ambiguous",
                    f"{len(matches)} service principals already exist for app_id "
                    f"{app_id}; not guessing which one to add a password to.",
                    False,
                    extra={"candidates": [sp.get("id") for sp in matches]},
                )

            if matches:
                service_principal_id = matches[0]["id"]
                created = False
            else:
                sp = await client.post("/servicePrincipals", {"appId": app_id})
                service_principal_id = sp["id"]
                created = True

            start_dt = _parse_graph_datetime(start_date_time) if start_date_time else datetime.now(
                timezone.utc
            )
            end_date_time = _format_graph_datetime(start_dt + timedelta(minutes=lifetime_minutes))

            password_credential: dict = {
                "displayName": display_name or _DEFAULT_DISPLAY_NAME,
                "endDateTime": end_date_time,
            }
            if start_date_time is not None:
                password_credential["startDateTime"] = start_date_time

            added = await client.post(
                f"/servicePrincipals/{service_principal_id}/addPassword",
                {"passwordCredential": password_credential},
            )
            payload = added if isinstance(added, dict) else {}
            return dump_json_capped(
                {
                    "service_principal_id": service_principal_id,
                    "app_id": app_id,
                    "created": created,
                    "secret_text": payload.get("secretText"),
                    "key_id": payload.get("keyId"),
                    "display_name": payload.get("displayName"),
                    "start_date_time": payload.get("startDateTime"),
                    "end_date_time": payload.get("endDateTime"),
                }
            )
        except GraphError as e:
            return e.to_envelope()
