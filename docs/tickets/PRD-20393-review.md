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

## Round 2 · 2026-11-06 · reviewed MSPbotsAIFramework/gdap-mcp dev/PRD-20393 @ 1d30bdd (base MSPbotsAIFramework/gdap-mcp origin/main @ 0a706f3)

Verdict: approved

### Scope

This is round 5 of PRD-20393, an implementation-error rework (see `PRD-20393-r5.md`'s "Rework
triage"): rounds 1-4 fixed `graph_remove_manager`/`graph_get_user` on `MSPbotsAIFramework/ms-graph-mcp`
only, but the Ginko offboarding workflows this ticket exists for call a separate, independently
maintained connector, `ms-graph-gdap` (repo `MSPbotsAIFramework/gdap-mcp`), which never received
those fixes. This round's actual code change lands entirely on `gdap-mcp`
(`app/graph_tools/users.py`, `tests/fake_microsoft.py`, `tests/test_flows.py`).
`ms-graph-mcp`'s own `dev/PRD-20393` (this repo) is doc-only this round — confirmed via
`git diff --stat origin/master...dev/PRD-20393` showing only `docs/tickets/PRD-20393-r5.md`,
one line in `-r4.md`, and `.ac.json`, no code change — so `ms-graph-mcp` needs no further
review this round beyond the doc itself.

### Findings

No must-fix found. Reviewed `gdap-mcp`'s `graph_remove_manager` and `graph_get_user` changes
against the design (`PRD-20393-r5.md` Tech design) and against the already-shipped,
already-QA-validated reference at `ms-graph-mcp@999f6f9` `src/graph_mcp/tools/users.py:417-471,752-818`:

- `app/graph_tools/users.py` (gdap-mcp): the `graph_remove_manager` read-then-delete flow
  (manager GET → existence-check-on-404 → DELETE, 404-on-DELETE treated as a benign race) and
  the `graph_get_user` `manager`-to-`$expand` routing plus null-injection are byte-for-byte
  equivalent in control flow to the reference implementation, adapted only to this repo's
  existing `client_factory`/`GraphError`/`dump_json_capped` names. `_USER_PROFILE_SELECT`
  gained the same four fields in the same position as the reference.
- No internal caller of `graph_remove_manager` exists in this repo
  (`grep -rn "graph_remove_manager\b" app/` — only docstring cross-references and the
  `registry.py` tool list), so the breaking response-shape change (`{"status", "user_id"}` →
  `{"user_id", "removed", "previous_manager", "reason"}`) cannot break any in-repo code path;
  it is the exact shape the requester's retest explicitly asked for (comment
  1600390000029562).
- Test-infrastructure extension (`tests/fake_microsoft.py`): `state.managers` +
  `GET`/`DELETE /users/{id}/manager` routes + `$select`/`$expand` honoring on the single-user
  GET route. Verified every current caller of that GET route already passes an explicit
  `$select` (`app/graph_tools/groups.py:228`, `app/graph_tools/users.py:746`), so tightening
  the fake cannot silently change any pre-existing test's expected response — consistent with
  the 143/143-passed result.
- No credential handling touched; no new Header, no cross-tenant call, no schema/migration
  (stateless Graph proxy, `state.managers` is test-fixture-only).
- Tests exercise behavior/contract (response shape, no-manager vs not-found disambiguation,
  manager-null injection), not implementation internals.

### Verified independently (re-ran, did not just trust the self-test doc)

- `uv run --frozen pytest -q` on `gdap-mcp@dev/PRD-20393` synced with `origin/main@0a706f3`,
  against a disposable `postgres:16-alpine` test container per this repo's README recipe:
  **143 passed, 0 failed** — matches the Self-test section's claim exactly.
- `git diff origin/main...dev/PRD-20393 -- app/graph_tools/users.py tests/fake_microsoft.py
  tests/test_flows.py | grep '^+' | grep -P '[\x{4e00}-\x{9fff}]'` → empty, confirming no
  Chinese introduced (repo-wide pre-existing hits are a known baseline, not this ticket's
  regression).
- `git diff --name-only origin/main...dev/PRD-20393` → `README.md` not listed, confirming the
  Connector section was genuinely untouched this round as the Self-test doc states.

### Suggestions

None beyond what Tech design's own Risks section already flagged as follow-up (shared-logic
extraction between `ms-graph-mcp`/`gdap-mcp`; auditing other `gdap-mcp` tools for the same
since-fixed-elsewhere gap) — both correctly scoped out of this round, not actioned here either.

Status: frozen @ MSPbotsAIFramework/gdap-mcp dev/PRD-20393 @ 1d30bdd
