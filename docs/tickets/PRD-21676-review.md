# PRD-21676 · Code review

Status: frozen @ a7fc711 (ms-graph-mcp) / 1de8faf (gdap-mcp)

## Round 1 · 2026-10-30 · reviewed ms-graph-mcp dev/PRD-21676 @ a7fc711 (base master @ e274955); gdap-mcp dev/PRD-21676 @ 1de8faf (base main @ 9ded92c)

Verdict: approved

### Scope

Both MCP repos (`MSPbotsAIFramework/ms-graph-mcp`, `MSPbotsAIFramework/gdap-mcp`) add `isAssignableToRole` to the `$select` list of `graph_get_group` and `graph_list_user_groups`, with matching docstring and README updates (ms-graph-mcp only; gdap-mcp's README has no per-tool table) and new tests in both repos. Diff reviewed: `git diff e274955..a7fc711` (ms-graph-mcp, excluding `docs/tickets/`) and `git diff 9ded92c..1de8faf` (gdap-mcp, full).

### Findings

No must-fix findings.

1. [suggestion] `app/graph_tools/groups.py` (gdap-mcp) — no issue in this diff, but confirming the pre-existing divergence the tech design already flagged as a non-goal (gdap-mcp's `graph_list_user_groups` queries plain `/memberOf` instead of ms-graph-mcp's `/memberOf/microsoft.graph.group` type-cast, PRD-20393's pagination fix): left as-is per the design's explicit Non-goals, not introduced or worsened by this change. No action needed in this ticket.

### Verification performed

- Independently re-ran both repos' full test suites on the exact synced-dev commits (not just read the Self-test section):
  - `ms-graph-mcp` @ `a7fc711` (`dev/PRD-21676`, synced with `master` @ `e274955`): `uv run pytest -q` → `184 passed`, 0 failed — matches the `[DEV]` stub and `docs/tickets/PRD-21676.md` Self-test section exactly.
  - `gdap-mcp` @ `1de8faf` (`dev/PRD-21676`, synced with `main` @ `9ded92c`): `uv run pytest -q` against a throwaway PostgreSQL 16 container (`TEST_PG_PORT` override, same fixture shape as the repo's own conftest) → `117 passed`, 0 failed — matches the Self-test section.
- Confirmed `git merge-base <dev sha> origin/<default>` equals the default branch HEAD for both repos — the dev branches are current, no further sync needed before merge.
- Confirmed the four `$select` edits (2 functions × 2 repos) are symmetric, additive-only, and the new field name is spelled identically (`isAssignableToRole`) in all four locations.
- Confirmed no Chinese characters were introduced by either diff (`grep -P '[\x{4e00}-\x{9fff}]'` over the added lines only — gdap-mcp's pre-existing Chinese comments elsewhere in the repo are untouched by this diff).
- Confirmed `ms-graph-mcp/README.md`'s Connector section (the `vendor-mcp-development/reference/readme-connector-section.md` block) is present byte-for-byte and untouched; this diff only edits two Tools-table row descriptions, which is in scope.
- Confirmed `gdap-mcp/README.md` has no per-tool table (`grep` for `graph_*` rows returns nothing), so no README update was owed there — consistent with the design's Current state note.
- Read the new tests in both repos (`tests/test_tools.py` additions in ms-graph-mcp; `tests/fake_microsoft.py` + `tests/test_flows.py` additions in gdap-mcp): each asserts the specific AC it claims (role-assignable → `true`, ordinary → passthrough `null` not coerced to `false`, existing fields unchanged, per-group correctness in list responses, tenant isolation in TC10) rather than re-testing implementation mechanics.
- No credential, header, or request-isolation code touched — the SOP's three "iron rules" (Header-only credentials, no disk/log persistence, per-request isolation) are unaffected by this change; not re-audited beyond confirming the diff doesn't touch that code path.
- `Track: vendor-mcp`, `Release order: any` (confirmed independently: neither repo's change depends on the other shipping first — no new header/field crosses the two repos).

### Conclusion

Change is a correct, minimal, symmetric implementation of the tech design: additive-only, both repos' full suites pass with 0 regressions on synced code, docs/README/tests all consistent with the design's Change list. No must-fix. Proceeding to merge both repos into their default branches, INT publish (one at a time), and the connector wiki check.
