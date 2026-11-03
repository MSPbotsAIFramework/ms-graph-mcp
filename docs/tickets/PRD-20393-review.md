# PRD-20393 · Code review

## Round 1 · 2026-11-03 · reviewed dev/PRD-20393 @ e39d9fb (base master@4ae1571)

Verdict: approved

### Scope

This is round 4 of PRD-20393, the first round reviewed under the 2026-10-29 three-stage
MCP flow (rounds 1-3 predate the separate review leg and are already merged into `master`).
Diff: `git diff 4ae1571...e39d9fb` — `src/graph_mcp/tools/users.py` (16 lines),
`tests/test_tools.py` (+110 lines, 5 new tests), `docs/tickets/PRD-20393-r4.{md,ac.json}`,
`docs/tickets/PRD-20393.ac.json`, one line in `docs/tickets/PRD-20393-r3.md`. No change to
`groups.py`, README, or any other tool.

### Independent verification performed this round

- Re-ran the full gate myself (uv not installed on this machine; substituted a
  `python3.12 -m venv` per the dev leg's own documented substitute): `python -m pytest -q`
  → 215 passed, 1 failed. The 1 failure is `test_tools_list_snapshot` on
  `graph_list_user_groups`'s description (547 > 500 chars) — confirmed pre-existing and
  unrelated: this round's diff does not touch `groups.py`, and the failure is tracked
  separately as red since PRD-21676.
- Ran the 5 new tests in isolation: `5 passed`.
- Read `graph_get_user` (`src/graph_mcp/tools/users.py:415-466`) directly: `manager_requested`
  is correctly tracked on both the `select`-given branch (pre-existing) and the default
  branch (new this round), and the null-injection (`if manager_requested and "manager" not in
  result: result["manager"] = None`) only fires when the key is absent — it never overwrites
  an existing value. This matches AC1 and the design's chosen Option B exactly.
- Read `graph_remove_manager` (`:745-818`) end to end: every return path produces
  `{"user_id", "removed", "previous_manager", "reason"}` or a `GraphError` envelope; there is
  no code path that returns a bare `{"status": "removed"}`. Confirms the design doc's Issue B
  claim that the 2026-11-02 retest's reported shape does not belong to this tool.
- Read `graph_remove_group_member` (`src/graph_mcp/tools/groups.py:335-362`): it does return
  `{"group_id": ..., "status": "removed"}` per group — exactly the shape the retest reported.
  Supports the design's "likely a different tool was called" explanation for Issue B.
- Checked `_USER_PROFILE_SELECT` (`users.py:35-45`): all four fields the retest called
  "still missing" (`onPremisesImmutableId`, `onPremisesSamAccountName`, `createdDateTime`,
  `lastPasswordChangeDateTime`) are present, confirming Issue C does not reproduce against
  this code.
- Measured the new docstring length directly (`len()`, no dedent/whitespace-collapse, matching
  what `test_tools_list_snapshot` actually checks): 474 raw chars, under the 500 budget —
  confirms the Self-test section's correction of its own earlier (wrong) budget math.
- Ran the repo's CJK scan on this round's own changed files (`users.py`, `test_tools.py`,
  `PRD-20393-r4.ac.json`): no hits. The 4 bracketed Chinese tags in `PRD-20393-r4.md`
  (`[不阻塞]`/`[已假设]`/`[改]`/`[新增]`) pre-date this dev leg (already in the design commit)
  and are pipeline-internal shorthand in a ticket doc, not connector/product content —
  consistent with the suggestion-only (non-blocking) precedent on PRD-21582's review.
- Confirmed `origin/master` is still at `4ae1571` (unchanged since this round's worktree was
  cut) — no base re-sync was needed before merging.

### Findings

1. [suggestion] `docs/tickets-index.md:9` — the PRD-20393 row still points at round 3
   (`PRD-20393-r3.md`), not this round's `PRD-20393-r4.md`. The dev leg's own Handoff section
   flagged this without picking a side: this repo pre-dates the 2026-10-29 convention that new
   vendor-mcp tickets don't maintain `docs/tickets-index.md` at all (`mcp-track.md` §2.4), but
   rounds 2-3 already established the pattern of keeping this repo's row current. Leaving it
   stale is consistent with the current convention and does not affect any behavior or
   deliverable — not a must-fix. No action taken; noting it here so it isn't silently missed by
   whoever next touches this ticket's docs.

No must-fix findings. The fix is narrow, additive, matches the design exactly, is backed by
3 new behavior tests (AC1) and 2 regression-confirmation tests (AC2/AC3) that were
independently re-verified above, and does not touch any code outside its stated scope.

Status: frozen @ e39d9fb
