from collections.abc import Callable
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN

_SELECT = (
    "id,displayName,state,createdDateTime,modifiedDateTime,"
    "conditions,grantControls,sessionControls"
)


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_list_conditional_access_policies(
        state: Annotated[
            Literal["enabled", "disabled", "enabledForReportingButNotEnforced"] | None,
            Field(description="Return only policies in this state. Omit to return all states."),
        ] = None,
    ) -> str:
        """List the tenant's Conditional Access policies (PRD-21579).

        Needs Policy.Read.All, not yet in the platform's requested scope set --
        calls return 403 until the tenant re-consents, see README.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        try:
            result = await client.get(
                "/identity/conditionalAccess/policies",
                params={"$select": _SELECT},
            )
            policies = result.get("value", []) if isinstance(result, dict) else []
            if state is not None:
                policies = [p for p in policies if p.get("state") == state]
            return dump_json_capped({"count": len(policies), "policies": policies})
        except GraphError as e:
            return e.to_envelope()
