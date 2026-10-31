# PRD-21582 · Code review

## Round 1 · 2026-10-31 · reviewed dev/PRD-21582 @ d882416 (base master @ 2e58da7)

Verdict: changes requested

### Findings

1. [must-fix] docs/tickets/PRD-21582.md:232 — The Self-test section's first bullet claims `uv run pytest` fails with `1 failed, 201 passed` on this branch (and `1 failed, 194 passed` on pristine `master` @ `2e58da7`), citing a specific pre-existing failure: `test_tools_list_snapshot` on `graph_list_user_groups: description too long (547 > 500 chars)`. This does not reproduce. Independently re-running the exact gate commands at the exact cited shas, with the committed `uv.lock` (unchanged by this ticket):
   - `dev/PRD-21582 @ d882416`: `uv sync && uv run pytest -q` → `202 passed` (3 consecutive runs, no flake). `uv run pytest -q -k test_tools_list_snapshot` → `1 passed`.
   - Measuring `graph_list_user_groups`'s actual registered tool description via `create_mcp_server(...).list_tools()`: `len(description) == 483`, which is `<= 500` and does not trip the assertion at `tests/test_tools.py:193`.
   - pristine `master @ 2e58da7` (separate worktree, same `uv sync`): `uv run pytest -q` → `195 passed` (not `1 failed, 194 passed` as claimed).
   The rest of the Self-test section's claims were independently verified and do hold (`ruff check`: 48/48 on branch/master, net zero new; `-k applications`: 7 passed; connector-section README diff byte-identical to the reference template; no CJK characters in any touched file; `tests/test_gdap_role_map.py` count bumped to 48 and passing). Only this one line is wrong, but it is wrong in a specific, detailed way (a named test, a named cause, exact byte counts on both sides of the merge) rather than a vague rounding error — that level of specific detail describing a failure that does not exist at the cited sha undermines trust in the self-test evidence this track relies on in place of a second reviewer re-running everything. Fix: correct this line to state the true baseline (`master @ 2e58da7`: 195 passed, 0 failed; this branch: 202 passed, 0 failed, 7 new) and double check no other line in Self-test/Handoff carries a similarly unverified claim before resubmitting.

### Fixes
(pending — see round 2 after rework)
