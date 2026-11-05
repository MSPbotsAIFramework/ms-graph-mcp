from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
    async def graph_create_invitation(
        invited_user_email_address: Annotated[
            str, Field(description='External email address to invite, e.g. "alice@fabrikam.com".')
        ],
        invite_redirect_url: Annotated[
            str,
            Field(
                description=(
                    'URL the guest is redirected to after redeeming the invitation, '
                    'e.g. "https://contoso.com/".'
                )
            ),
        ],
        send_invitation_message: Annotated[
            bool, Field(description="Whether Graph emails the invitation. Defaults to true.")
        ] = True,
        invited_user_display_name: Annotated[
            str | None, Field(description="Display name to give the new guest user.")
        ] = None,
        message_language: Annotated[
            str | None, Field(description='Invitation email locale, e.g. "en-US".')
        ] = None,
        customized_message_body: Annotated[
            str | None, Field(description="Custom text included in the invitation email body.")
        ] = None,
        cc_recipients: Annotated[
            list[str] | None,
            Field(description="Extra email addresses to CC on the invitation email."),
        ] = None,
    ) -> str:
        """Invite an external email address as an Entra ID B2B guest user.

        Returns the guest's directory id (chain directly into
        graph_assign_groups), the redemption URL, and the invitation status.
        Not idempotent — Graph decides what happens if the email already
        corresponds to an existing guest.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        body: dict = {
            "invitedUserEmailAddress": invited_user_email_address,
            "inviteRedirectUrl": invite_redirect_url,
            "sendInvitationMessage": send_invitation_message,
        }
        if invited_user_display_name is not None:
            body["invitedUserDisplayName"] = invited_user_display_name

        message_info: dict = {}
        if message_language is not None:
            message_info["messageLanguage"] = message_language
        if customized_message_body is not None:
            message_info["customizedMessageBody"] = customized_message_body
        if cc_recipients is not None:
            message_info["ccRecipients"] = [
                {"emailAddress": {"address": address}} for address in cc_recipients
            ]
        if message_info:
            body["invitedUserMessageInfo"] = message_info

        try:
            result = await client.post("/invitations", body)
            payload = result if isinstance(result, dict) else {}
            invited_user = payload.get("invitedUser") or {}
            return dump_json_capped(
                {
                    "invited_user_id": invited_user.get("id"),
                    "invited_user_email_address": payload.get("invitedUserEmailAddress"),
                    "invite_redeem_url": payload.get("inviteRedeemUrl"),
                    "status": payload.get("status"),
                }
            )
        except GraphError as e:
            return e.to_envelope()
