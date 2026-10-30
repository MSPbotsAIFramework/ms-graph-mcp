# PRD-21578 · Code review

Status: frozen @ 48d2a50

## Round 1 · 2026-10-30 · reviewed dev/PRD-21578 48d2a50 (base master d2ee761)

Verdict: approved

### Findings

No must-fix findings.

1. [suggestion] `src/graph_mcp/tools/sites.py:567` (pre-existing, not introduced by this diff) — `graph_delete_file`'s `@mcp.tool(...)` annotation does not set `readOnlyHint` explicitly (relies on the library default), while the new `graph_delete_message` sets it explicitly (`readOnlyHint=False`). Not a defect in this ticket — the new tool's explicit form is strictly more correct and was verified by `test_delete_message_annotations`. Worth aligning the two older sibling tools (`graph_delete_file`, `graph_remove_managed_device`) the same way in a future, unrelated cleanup ticket; out of scope here per `mcp-track.md` §"本单碰到的模块里清理" (this ticket did not touch `sites.py`/`devices.py`).

### Verification performed

- Re-ran `uv run pytest -q` on `dev/PRD-21578 @ 48d2a50` (synced on top of `master @ d2ee761`): `189 passed` — matches the Self-test section exactly.
- Re-ran the Chinese-character gate (`grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv .`): only hits are in `docs/tickets/PRD-21676.md:28,221`, a different, already-frozen ticket doc brought in by the `master` sync — not introduced by this ticket, matches the Self-test's own disclosure.
- Diffed `README.md` lines 5–75 against `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md`: byte-for-byte identical.
- Read `src/graph_mcp/tools/mail.py`'s new `graph_delete_message` function against the design's Data & API contract: implementation matches verbatim (request shape, 404-as-success, error envelope passthrough, response fields).
- Compared the new tool against the three cited precedents (`graph_delete_file` in `sites.py:567-593`, `graph_remove_managed_device` in `devices.py:52-80`): same idempotent-delete shape, same `GraphClient.delete()` primitive, same `user_id`/base-path convention as `graph_get_message`.
- Checked `GraphError`/`_STATUS_TO_CODE` in `api_client.py:36-43`: confirms 403 maps to `unauthorized`, matching `test_delete_message_surfaces_non_404_error`'s assertion and the ac.json evidence.
- Checked `docs/gdap-role-map.yaml` and `tests/test_gdap_role_map.py` diff: new entry and bumped count (45 → 46) are consistent; `test_gdap_role_map_matches_registered_tools_and_readme` is part of the 189 passing tests above.
- Checked scope against `legs/review.md` R3 table: no UI, no migration (N/A for MCP repos), no new dependency, no cross-repo header/field added (tool reuses the existing `X-Ms-Graph-Token` auth, nothing new for a receiving side to tolerate per `mcp-track.md` §1.2), credentials stay request-scoped (no new storage/logging).
- AC coverage: AC1–AC6 each have a passing automated test (TC1–TC6, see `docs/tickets/PRD-21578.ac.json`); TC7 (real-tenant verification) is recorded `not_run` with a stated reason (no real Microsoft 365 tenant available) — not a blocker per `references/mcp-track.md` §2.5/§3, and is tracked in README Known Gaps.

### Conclusion

The diff is a straightforward, well-precedented additive change: one new idempotent-delete tool copied from two existing reviewed patterns in the same repo, plus consistent documentation updates (README tools table, scope union, scope narrative, GDAP role map) all covered by the repo's own consistency test. No behavior of any existing tool changed. Approved for merge into `master`, INT publish, and connector wiki check.
