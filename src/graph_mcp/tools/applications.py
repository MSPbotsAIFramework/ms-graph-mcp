from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN, skiptoken

# Same convention as users.py/groups.py (PRD-21582): our own ceiling on how
# many results a list tool returns to the agent (SOP: default <=50, hard cap
# <=200), separate from Graph's own $top per-page maximum (999).
_DEFAULT_MAX_RESULTS = 50
_HARD_CAP_MAX_RESULTS = 200
_GRAPH_TOP_MAX = 999

# The register's own HTTP contract (item 14): appId, displayName and
# passwordCredentials only -- no keyCredentials (certificates), not asked for.
_APPLICATION_SELECT = "appId,displayName,passwordCredentials"


def _days_until_expiry(end_date_time: str | None, now: datetime) -> int | None:
    """Days from now until end_date_time, negative once the secret has
    expired. None when Graph did not return an end_date_time at all (should
    not happen for a real passwordCredentials entry, but a tool should not
    crash on a missing optional field)."""
    if not end_date_time:
        return None
    try:
        end = datetime.fromisoformat(end_date_time.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (end - now).days


def _map_secret(credential: dict, now: datetime) -> dict:
    end_date_time = credential.get("endDateTime")
    return {
        "key_id": credential.get("keyId"),
        "display_name": credential.get("displayName"),
        "start_date_time": credential.get("startDateTime"),
        "end_date_time": end_date_time,
        "hint": credential.get("hint"),
        "days_until_expiry": _days_until_expiry(end_date_time, now),
    }


def _map_application(application: dict, now: datetime) -> dict:
    return {
        "app_id": application.get("appId"),
        "display_name": application.get("displayName"),
        # AC2: an app with no client secrets still appears, with secrets: [].
        "secrets": [_map_secret(c, now) for c in application.get("passwordCredentials") or []],
    }


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_list_applications(
        max_results: Annotated[
            int, Field(description="Max applications per page (default 50, hard cap 200).")
        ] = _DEFAULT_MAX_RESULTS,
        page_token: Annotated[
            str | None,
            Field(description="next_page_token from the previous page; omit for the first page."),
        ] = None,
    ) -> str:
        """List the tenant's Entra ID application (app) registrations and
        each client secret's expiry metadata, for early warning before a
        secret expires (PRD-21582).

        Each secret carries a computed days_until_expiry (negative once
        already expired) so the caller does not parse dates itself. One
        Graph page per call; when has_more is true, call again with
        next_page_token. Read-only: never creates, rotates, or deletes a
        secret or an application.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        max_results = max(1, min(max_results, _HARD_CAP_MAX_RESULTS))
        params: dict = {
            "$select": _APPLICATION_SELECT,
            "$top": str(min(max_results, _GRAPH_TOP_MAX)),
        }
        if page_token:
            params["$skiptoken"] = page_token

        try:
            result = await client.get("/applications", params=params)
            raw_apps = result.get("value", [])[:max_results]
            now = datetime.now(UTC)
            applications = [_map_application(a, now) for a in raw_apps]
            next_token = skiptoken(result.get("@odata.nextLink"))
            return dump_json_capped(
                {
                    "count": len(applications),
                    "applications": applications,
                    "has_more": next_token is not None,
                    "next_page_token": next_token,
                }
            )
        except GraphError as e:
            return e.to_envelope()
