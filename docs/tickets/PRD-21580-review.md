# PRD-21580 · Code review

## Round 1 · 2026-10-30 · reviewed 70ee4bc (base d2ee761)

Verdict: approved

### Findings

None. No must-fix, no suggestions.

### Notes

- Scope: `git diff d2ee761...70ee4bc` touches `README.md`, `docs/gdap-role-map.yaml`, `docs/tickets/PRD-21580.{md,ac.json}`, `src/graph_mcp/server.py`, `src/graph_mcp/tools/conditional_access.py` (new), `tests/test_gdap_role_map.py`, `tests/test_tools.py`. All within the technical design's change list; no unrelated files touched.
- Correctness: `graph_list_named_locations` (src/graph_mcp/tools/conditional_access.py:29-105) follows the existing `client_factory()` -> `NO_TOKEN` guard -> `client.get()` -> `dump_json_capped()` / `GraphError.to_envelope()` pattern used by every other tool in this connector (e.g. `graph_get_group`, `graph_list_domains`). `_location_type()` (conditional_access.py:14-23) maps unknown `@odata.type` values to `"unknown"` instead of raising, so a future third Graph location type degrades gracefully rather than crashing the tool — correct defensive handling, matches AC1/AC2's requirement that `isTrusted` not be fabricated on country-type results (verified: `_shape_location` only spreads the source payload plus `location_type`, so a payload without `isTrusted` never gets one).
- Pagination: no-id branch caps at `min(max_results, 200)` (conditional_access.py:65) and surfaces `has_more`/`next_page_token` via the existing `skiptoken()` helper, consistent with `graph_list_group_members`'s contract (AC4).
- Reuse: no new dependencies; reuses `GraphClient`, `GraphError`, `dump_json_capped`, `NO_TOKEN`, `skiptoken` as designed. The `_DEFAULT_MAX_RESULTS`/`_HARD_CAP_MAX_RESULTS` constants are re-declared locally rather than imported from `groups.py` — this was an explicit, justified trade-off in the tech design ("Reuse & cleanup"), not an oversight; not flagged as a finding.
- Security: credentials remain header-only via `client_factory()`/`GatewayTokenMiddleware`; no new persistence, no new logging. `Policy.Read.All` is a newly-documented, self-contained scope — no re-consent dependency on another in-flight ticket.
- Tests: TC1-TC6 and TC8 are automated and pass (`uv run pytest -v -k "test_list_named_locations or test_gdap_role_map_matches_registered_tools_and_readme"` -> 7 passed, reproduced independently on `70ee4bc`). TC7 (real-tenant 403 path) is correctly recorded as `blocked`/needs-a-real-vendor-account per `references/mcp-track.md` section 3 — not a gate per that policy.
- Full gate re-run (`uv run pytest -q` on `70ee4bc`, independently reproduced): `189 passed, 1 failed`. The failure (`test_tools_list_snapshot` — `graph_list_user_groups: description too long`, 547 > 500 chars) is pre-existing: reproduced the identical failure on pristine `master` @ `d2ee761` (PRD-21676's already-merged docstring change) with `dev/PRD-21580`'s changes absent entirely (183 passed, 1 failed with the same assertion). Zero new failures introduced by this diff — matches the `[DEV]` stub's claim.
- Consistency guard: `tests/test_gdap_role_map.py`'s `assert len(role_map) == 46` bump and the new `docs/gdap-role-map.yaml` entry (`Security Reader`, matching the README row) keep the repo's own three-way consistency check (`check_consistency`) passing without touching its logic — confirmed by the passing `test_gdap_role_map_matches_registered_tools_and_readme` run above.
- README: Tools-table row present (README.md:166) with matching permission/role; Overview tool count recomputed 45 -> 46; `## MSPbots Connector` block (lines 5-75) untouched by this diff, outside the changed Overview line (76) — no drift from `reference/readme-connector-section.md`.
- No schema/migration (connector is stateless); no UI surface (N/A for MCP); no parameter stacking (single new optional param added incrementally, not a boolean flag bolted onto an existing tool); no dead code introduced or left behind.

Status: frozen @ 70ee4bc
