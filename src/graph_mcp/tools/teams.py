from collections.abc import Callable
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN, missing_scope_error, odata_quote, skiptoken

# Per-module constants, same convention as groups.py/policies.py (not
# exported from a shared location -- PRD-22034 Reuse & cleanup).
_DEFAULT_PAGE_SIZE = 50
_HARD_CAP_PAGE_SIZE = 200
_GRAPH_TOP_MAX = 999

_TEAM_SELECT = "id,displayName,description,visibility"
_CHANNEL_SELECT = "id,displayName,membershipType,webUrl"
_CHANNEL_DETAIL_SELECT = "id,displayName,description,membershipType,email,webUrl,isArchived"


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_list_teams(
        name_prefix: Annotated[
            str | None,
            Field(
                description="Prefix match on the team's displayName. Omit to list all teams (still capped by page_size)."
            ),
        ] = None,
        user_id: Annotated[
            str | None,
            Field(
                description="List only this user's joined teams (GUID or userPrincipalName). When also given with name_prefix, the prefix is applied client-side on the returned page."
            ),
        ] = None,
        page_size: Annotated[
            int, Field(description="Max teams per page (default 50, hard cap 200).")
        ] = _DEFAULT_PAGE_SIZE,
        page_token: Annotated[
            str | None,
            Field(description="next_page_token from the previous page; omit for the first page."),
        ] = None,
    ) -> str:
        """Find a Microsoft Teams team by name prefix or by a user's membership.

        One page per call, same pagination contract as graph_list_groups:
        has_more=true means call again with next_page_token. Needs
        Team.ReadBasic.All -- a tenant that has not consented yet gets a
        structured error naming that scope, not a generic 403 (PRD-22034).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        page_size = max(1, min(page_size, _HARD_CAP_PAGE_SIZE))
        params: dict = {
            "$select": _TEAM_SELECT,
            "$top": str(min(page_size, _GRAPH_TOP_MAX)),
        }
        if page_token:
            params["$skiptoken"] = page_token

        try:
            if user_id:
                result = await client.get(f"/users/{user_id}/joinedTeams", params=params)
            else:
                if name_prefix:
                    params["$filter"] = f"startswith(displayName,'{odata_quote(name_prefix)}')"
                result = await client.get("/teams", params=params)
        except GraphError as e:
            return missing_scope_error(e, "Team.ReadBasic.All")

        teams = result.get("value", []) if isinstance(result, dict) else []
        if user_id and name_prefix:
            prefix = name_prefix.lower()
            teams = [t for t in teams if (t.get("displayName") or "").lower().startswith(prefix)]
        next_token = skiptoken(result.get("@odata.nextLink")) if isinstance(result, dict) else None
        return dump_json_capped(
            {
                "count": len(teams),
                "teams": teams,
                "has_more": next_token is not None,
                "next_page_token": next_token,
            }
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_list_channels(
        team_id: Annotated[str, Field(description="The team's id, from graph_list_teams.")],
        membership_type: Annotated[
            Literal["standard", "private", "shared"] | None,
            Field(
                description="Return only channels of this type. Omit for Graph's default (standard channels only -- private/shared channels only appear when explicitly filtered)."
            ),
        ] = None,
    ) -> str:
        """List a team's channels: id, displayName, membershipType, webUrl.

        Not paginated -- a team's channel count is well below one Graph
        page. Needs Channel.ReadBasic.All -- a tenant that has not
        consented yet gets a structured error naming that scope, not a
        generic 403 (PRD-22034).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        params: dict = {"$select": _CHANNEL_SELECT}
        if membership_type:
            params["$filter"] = f"membershipType eq '{membership_type}'"

        try:
            result = await client.get(f"/teams/{team_id}/channels", params=params)
        except GraphError as e:
            return missing_scope_error(e, "Channel.ReadBasic.All")

        channels = result.get("value", []) if isinstance(result, dict) else []
        return dump_json_capped(
            {"team_id": team_id, "count": len(channels), "channels": channels}
        )

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_get_channel(
        team_id: Annotated[str, Field(description="The team's id, from graph_list_teams.")],
        channel_id: Annotated[
            str, Field(description="The channel's id, from graph_list_channels.")
        ],
    ) -> str:
        """Get one channel's details: displayName, description, membershipType,
        webUrl, isArchived, and email.

        email is always present -- "" when the channel has no configured
        email, never a missing key or null, so a caller never has to
        special-case it. Needs Channel.ReadBasic.All -- a tenant that has
        not consented yet gets a structured error naming that scope, not a
        generic 403 (PRD-22034).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        try:
            result = await client.get(
                f"/teams/{team_id}/channels/{channel_id}",
                params={"$select": _CHANNEL_DETAIL_SELECT},
            )
        except GraphError as e:
            return missing_scope_error(e, "Channel.ReadBasic.All")

        return dump_json_capped(
            {
                "id": result.get("id"),
                "displayName": result.get("displayName"),
                "description": result.get("description"),
                "membershipType": result.get("membershipType"),
                "email": result.get("email") or "",
                "webUrl": result.get("webUrl"),
                "isArchived": result.get("isArchived"),
            }
        )
