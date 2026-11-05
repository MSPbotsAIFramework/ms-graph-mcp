from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_get_security_defaults_policy() -> str:
        """Read whether the tenant's Security Defaults policy is enabled
        (MFA reporting; PRD-21581, closing gap item 13 of the Rewst-to-MSPbots
        migration register).

        No parameters -- the tenant is implied by the caller's token, same as
        graph_list_gdap_roles and graph_check_license_stock.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        try:
            result = await client.get(
                "/policies/identitySecurityDefaultsEnforcementPolicy",
                params={"$select": "id,displayName,description,isEnabled"},
            )
            return dump_json_capped(result)
        except GraphError as e:
            return e.to_envelope()
