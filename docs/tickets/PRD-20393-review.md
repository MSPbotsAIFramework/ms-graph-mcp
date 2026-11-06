# PRD-20393 · Code review

Status: frozen @ MSPbotsAIFramework/gdap-mcp dev/PRD-20393 @ 1d30bdd

## Round 1 · 2026-11-06 · reviewed MSPbotsAIFramework/gdap-mcp dev/PRD-20393 @ 1d30bdd (base origin/main @ 0a706f3)

Verdict: approved

### Scope

This round's actual code change lands entirely on `MSPbotsAIFramework/gdap-mcp` (`app/graph_tools/users.py`, `tests/fake_microsoft.py`, `tests/test_flows.py`). `MSPbotsAIFramework/ms-graph-mcp`'s `dev/PRD-20393` (this repo) is doc-only this round (`docs/tickets/PRD-20393-r5.md`, `-r4.md` link, `.ac.json`) — confirmed via `git diff --stat origin/master...dev/PRD-20393` showing only the three doc files, no code change, so `ms-graph-mcp` needs no review this round beyond the doc itself.

### Findings

No must-fix found. Reviewed `gdap-mcp`'s `graph_remove_manager` and `graph_get_user` changes against the design (`PRD-20393-r5.md` Tech design) and against the already-shipped, already-QA-validated reference at `ms-graph-mcp@999f6f9` `src/graph_mcp/tools/users.py:417-471,752-818`:

- `app/graph_tools/users.py` (gdap-mcp): the `graph_remove_manager` read-then-delete flow (manager GET → existence-check-on-404 → DELETE, 404-on-DELETE treated as a benign race) and the `graph_get_user` `manager`-to-`$expand` routing plus null-injection are byte-for-byte equivalent in control flow to the reference implementation, adapted only to this repo's existing `client_factory`/`GraphError`/`dump_json_capped` names. `_USER_PROFILE_SELECT` gained the same four fields in the same position as the reference.
- No internal caller of `graph_remove_manager` exists in this repo (`grep -rn "graph_remove_manager\b" app/` — only docstring cross-references and the `registry.py` tool list), so the breaking response-shape change (`{"status", "user_id"}` → `{"user_id", "removed", "previous_manager", "reason"}`) cannot break any in-repo code path; it is the exact shape the requester's retest explicitly asked for (comment 1600390000029562).
- Test-infrastructure extension (`tests/fake_microsoft.py`): `state.managers` + `GET`/`DELETE /users/{id}/manager` routes + `$select`/`$expand` honoring on the single-user GET route. Verified every current caller of that GET route already passes an explicit `$select` (`app/graph_tools/groups.py:228`, `app/graph_tools/users.py:746`), so tightening the fake cannot silently change any pre-existing test's expected response — consistent with the 143/143-passed result.
- No credential handling touched; no new Header, no cross-tenant call, no schema/migration (stateless Graph proxy, `state.managers` is test-fixture-only).
- Tests exercise behavior/contract (response shape, no-manager vs not-found disambiguation, manager-null injection), not implementation internals.

### Verified independently (re-ran, did not just trust the self-test doc)

- `uv run --frozen pytest -q` on `gdap-mcp@dev/PRD-20393` synced with `origin/main@0a706f3`, against a disposable `postgres:16-alpine` test container per this repo's README recipe: **143 passed, 0 failed** — matches the Self-test section's claim exactly.
- `git diff origin/main...dev/PRD-20393 -- app/graph_tools/users.py tests/fake_microsoft.py tests/test_flows.py | grep '^+' | grep -P '[\x{4e00}-\x{9fff}]'` → empty, confirming no Chinese introduced (repo-wide pre-existing hits are a known baseline, not this ticket's regression).
- `git diff --name-only origin/main...dev/PRD-20393` → `README.md` not listed, confirming the Connector section was genuinely untouched this round as the Self-test doc states.

### Suggestions

None beyond what Tech design's own Risks section already flagged as follow-up (shared-logic extraction between `ms-graph-mcp`/`gdap-mcp`; auditing other `gdap-mcp` tools for the same since-fixed-elsewhere gap) — both correctly scoped out of this round, not actioned here either.
