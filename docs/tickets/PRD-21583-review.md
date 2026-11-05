# PRD-21583 · Code review

## Round 1 · 2026-11-05 · reviewed dev/PRD-21583 @ c8bc43d (base master @ 080f4ef)

Verdict: approved

Status: frozen @ c8bc43d

### Scope

`git diff origin/master(080f4ef)...c8bc43d` — 7 files: `src/graph_mcp/tools/users.py`, `README.md`, `docs/gdap-role-map.yaml`, `tests/test_tools.py`, `tests/test_gdap_role_map.py`, `docs/tickets/PRD-21583.md`, `docs/tickets/PRD-21583.ac.json`.

### Findings

None.

### Verification performed

1. Re-ran the full gate on `c8bc43d`: `uv run pytest -q` -> `221 passed, 1 failed` (`test_tools_list_snapshot`, `graph_list_user_groups` description 547>500 chars), matching the Self-test section exactly.
2. Confirmed the 1 failure pre-exists on pristine `origin/master @ 080f4ef` by running the same test in a throwaway detached worktree before this ticket's merge: same assertion, same 547-char count. Not introduced by this ticket (WARN, correctly documented in Self-test, `REVIEW.md` §4 baseline-red exemption applies).
3. `uv run pytest -v -k delete_auth_method` -> 6 passed (TC1/TC2/TC3/TC4/TC5/TC7).
4. `diff <(sed -n '5,75p' README.md) reference/readme-connector-section.md` -> identical.
5. `git diff origin/master...HEAD -- src tests README.md docs/gdap-role-map.yaml | grep CJK` -> no hits.
6. Tool contract: credentials read only via the existing per-request `X-Ms-Graph-Token` (no new header), no state shared across calls, error envelope reuses `GraphError.to_envelope()` (403->unauthorized, 5xx->upstream_error, verified by TC3/TC5 tests), idempotent-404 convention matches `graph_remove_manager`/`graph_remove_managed_device`. Annotations (`readOnlyHint=False, destructiveHint=True, idempotentHint=True`) correct for a destructive delete.
7. Docstring 356 chars (<=500), first line 61 chars (<=100) — within SOP §14 limits; test_tools_list_snapshot's own <=500 assertion passes for this tool.
8. Merge conflict resolution (README overview count, Known Gaps bullet, two hardcoded count assertions) documented per-block in the "Merge" section of `PRD-21583.md` with no behavioral judgment calls — satisfies `REVIEW.md` §2.7.
9. TC6 (manual, needs real vendor account) correctly recorded as `blocked` with reason, per `mcp-track.md` §3 "missing a real vendor account does not block this track" — not a gate failure.
10. No new dependency, no duplicated logic versus the three existing idempotent-delete tools cited in the tech design; change is purely additive (no existing tool signature/behavior changed).

No must-fix found. Approved for merge.
