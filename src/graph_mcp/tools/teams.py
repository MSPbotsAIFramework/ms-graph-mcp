import html
from collections.abc import Callable
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped, error_envelope
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

# graph_send_channel_message (PRD-22035).
_SEND_SCOPE = "ChannelMessage.Send"
# Same cap PRD-22030 proposed for individual mentions; there is no @team /
# @channel mention support at all, so broad mentions cannot be built.
_MAX_MENTIONS = 5
# Graph rejects a chatMessage whose body is over roughly 28 KB. Checked up
# front so an oversized body is refused clearly instead of half-posted or
# truncated.
_MAX_BODY_BYTES = 28_000


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

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
        )
    )
    async def graph_send_channel_message(
        team_id: Annotated[str, Field(description="The team's id, from graph_list_teams.")],
        channel_id: Annotated[
            str, Field(description="The channel's id, from graph_list_channels.")
        ],
        body: Annotated[str, Field(description="Message body, plain text or HTML (see body_content_type).")],
        body_content_type: Annotated[
            Literal["text", "html"], Field(description='"text" or "html".')
        ] = "text",
        subject: Annotated[
            str | None, Field(description="Optional subject line shown above the post.")
        ] = None,
        importance: Annotated[
            Literal["normal", "high", "urgent"], Field(description="Post importance.")
        ] = "normal",
        mention_user_ids: Annotated[
            list[str] | None,
            Field(
                description=f"Users to @mention (object id or userPrincipalName), at most {_MAX_MENTIONS}. The mentions are placed at the start of the post."
            ),
        ] = None,
    ) -> str:
        """Post a new message to a Teams channel as the signed-in user.

        One post per call; no thread replies. Irreversible once sent.
        Returns message_id and webUrl. Delegated Microsoft Graph connector
        only: needs ChannelMessage.Send and the signed-in user must be a
        member of the channel. The app-only connector cannot post (Graph
        has no application permission for this).
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        mention_ids = list(dict.fromkeys(m.strip() for m in (mention_user_ids or []) if m.strip()))
        if len(mention_ids) > _MAX_MENTIONS:
            return error_envelope(
                "invalid_argument",
                f"At most {_MAX_MENTIONS} users can be mentioned in one post, got {len(mention_ids)}.",
                False,
            )

        mentions: list[dict] = []
        for i, user_id in enumerate(mention_ids):
            try:
                user = await client.get(f"/users/{user_id}", params={"$select": "id,displayName"})
            except GraphError as e:
                return e.to_envelope()
            name = (user or {}).get("displayName") or user_id
            mentions.append(
                {
                    "id": i,
                    "mentionText": name,
                    "mentioned": {
                        "user": {
                            "id": (user or {}).get("id") or user_id,
                            "displayName": name,
                            "userIdentityType": "aadUser",
                        }
                    },
                }
            )

        content_type = body_content_type
        content = body
        if mentions:
            # Mentions only render in an HTML body, and each <at id="n"> tag
            # must match the mentions[n] entry. A plain-text body is escaped
            # so it still reads as text once the type becomes html.
            if content_type == "text":
                content = html.escape(content).replace("\n", "<br>")
                content_type = "html"
            tags = " ".join(
                f'<at id="{m["id"]}">{html.escape(m["mentionText"])}</at>' for m in mentions
            )
            content = f"<p>{tags}</p>{content}"

        size = len(content.encode("utf-8"))
        if size > _MAX_BODY_BYTES:
            return error_envelope(
                "invalid_argument",
                f"Message body is {size} bytes; Teams accepts at most about {_MAX_BODY_BYTES}. "
                "Shorten it; it is not truncated.",
                False,
                extra={"size": size, "limit": _MAX_BODY_BYTES},
            )

        payload: dict = {
            "body": {"contentType": content_type, "content": content},
            "importance": importance,
        }
        if subject:
            payload["subject"] = subject
        if mentions:
            payload["mentions"] = mentions

        try:
            result = await client.post(f"/teams/{team_id}/channels/{channel_id}/messages", payload)
        except GraphError as e:
            if e.status_code == 403:
                return error_envelope(
                    "unauthorized",
                    f"Teams refused the post. Check that: the connector is the delegated "
                    f"Microsoft Graph connector (the app-only one cannot post to channels); "
                    f"an admin has consented to {_SEND_SCOPE}; and the signed-in user is a "
                    f"member of this channel.",
                    False,
                    extra={"required_scope": _SEND_SCOPE, "graph_status": 403},
                )
            return e.to_envelope()

        result = result if isinstance(result, dict) else {}
        return dump_json_capped(
            {
                "status": "sent",
                "message_id": result.get("id"),
                "webUrl": result.get("webUrl"),
                "sent_at": result.get("createdDateTime"),
                "team_id": team_id,
                "channel_id": channel_id,
            }
        )
