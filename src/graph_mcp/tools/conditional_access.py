from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import GraphClient, GraphError
from ._common import NO_TOKEN, skiptoken

# Same list-cap convention as groups.py/users.py (SOP: default <=50, hard
# cap <=200); re-declared locally rather than imported to avoid a cross-module
# dependency for two integers (PRD-21580 design, "Reuse & cleanup").
_DEFAULT_MAX_RESULTS = 50
_HARD_CAP_MAX_RESULTS = 200


def _location_type(odata_type: str) -> str:
    """Map a namedLocation's @odata.type to a short, stable discriminator.

    Graph currently defines two concrete types (ipNamedLocation,
    countryNamedLocation); anything else maps to "unknown" so a future
    third type doesn't crash this tool, it just shows up unclassified.
    """
    if odata_type.endswith("ipNamedLocation"):
        return "ip"
    if odata_type.endswith("countryNamedLocation"):
        return "country"
    return "unknown"


def _shape_location(location: dict) -> dict:
    odata_type = location.get("@odata.type", "") or ""
    return {**location, "location_type": _location_type(odata_type)}


def register(mcp: FastMCP, client_factory: Callable[[], GraphClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
    async def graph_list_named_locations(
        location_id: Annotated[
            str | None,
            Field(
                description=(
                    "Conditional Access named location object id (GUID). "
                    "Omit to list all named locations in the tenant."
                )
            ),
        ] = None,
        max_results: Annotated[
            int,
            Field(
                description="Max locations per page when location_id is omitted (default 50, hard cap 200)."
            ),
        ] = _DEFAULT_MAX_RESULTS,
        page_token: Annotated[
            str | None,
            Field(
                description=(
                    "next_page_token from a previous no-id call; omit for the first "
                    "page. Ignored when location_id is given."
                )
            ),
        ] = None,
    ) -> str:
        """Resolve a Conditional Access named location id to its details, e.g. to
        turn a CA policy's location id into a readable name, or list all named
        locations in the tenant.

        A named location is either an IP range set (location_type="ip", has
        ipRanges/isTrusted) or a country/region set (location_type="country",
        has countriesAndRegions). When location_id is omitted and has_more is
        true, call again with next_page_token for the rest.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN

        try:
            if location_id:
                result = await client.get(
                    f"/identity/conditionalAccess/namedLocations/{location_id}"
                )
                return dump_json_capped(_shape_location(result))

            capped = max(1, min(max_results, _HARD_CAP_MAX_RESULTS))
            params: dict = {"$top": str(capped)}
            if page_token:
                params["$skiptoken"] = page_token
            result = await client.get(
                "/identity/conditionalAccess/namedLocations", params=params
            )
            locations = [_shape_location(loc) for loc in result.get("value", [])[:capped]]
            next_token = skiptoken(result.get("@odata.nextLink"))
            return dump_json_capped(
                {
                    "count": len(locations),
                    "named_locations": locations,
                    "has_more": next_token is not None,
                    "next_page_token": next_token,
                }
            )
        except GraphError as e:
            return e.to_envelope()
