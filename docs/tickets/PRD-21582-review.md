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

Must-fix 1 (docs/tickets/PRD-21582.md:232) — **disputed, no change made; evidence below for the next review round.**

Re-ran the exact gate at the exact cited shas, in fresh isolated `git worktree`s off the bare cache (no stale `.venv`/pyc carried over), three times each for flake-checking:

- `dev/PRD-21582 @ d882416` (the sha round 1 cited): `uv sync -q && uv run pytest -q` → **`1 failed, 201 passed`** (ran 3x, identical every time: `test_tools_list_snapshot` fails, `graph_list_user_groups: description too long, assert 547 <= 500`). `uv run pytest -q -k test_tools_list_snapshot` alone, 3x → same failure every time, never `1 passed`.
- `dev/PRD-21582 @ 1e522e7` (current HEAD, includes this review doc's own round-1 commit): same failure, same `547`, `1 failed, 201 passed` (4 consecutive runs).
- pristine `master @ 2e58da7` (separate `git worktree add --detach` off the bare cache, same `uv sync -q`): `uv run pytest -q` → **`1 failed, 194 passed`** — matches the original Self-test bullet's claimed baseline exactly, not the `195 passed, 0 failed` this finding cited.

So the original Self-test line reproduces for me at all three shas, deterministically, with no flake observed. Tracked down why round 1's own re-verification landed on `483`/`195 passed, 0 failed` instead:

- Measured the description the same way `tests/test_tools.py:193` and the real server do — calling `create_mcp_server(Settings())` then `await mcp.list_tools()` and reading `.description` off the returned `Tool` for `graph_list_user_groups` — at `d882416`: `len(description) == 547`, and `repr()` shows the raw docstring **with its original indentation and surrounding blank lines intact** (FastMCP/`mcp==1.28.1` does not dedent or strip tool descriptions before registering them; confirmed by direct `repr()` inspection, not an assumption).
- Reproduced `483` only by running `inspect.cleandoc()` (dedent + strip) over that same raw docstring first: `len(inspect.cleandoc(raw)) == 482` (one char off `483`, likely a transcription variant of the same cleaning, e.g. a different dedent/strip helper) — i.e. `483`/`482` is what you get by cleaning the docstring before measuring it, which is not what `tests/test_tools.py:193` does and not what the registered tool's `.description` actually contains at runtime.

That is the most likely source of the discrepancy: round 1's independent check appears to have measured a dedented/cleaned copy of the docstring rather than the raw `Tool.description` FastMCP actually serves (the thing the assertion and the real server both operate on). It is not a flake — the string is a static Python literal, byte-identical across runs by construction.

Double-checked the rest of the Self-test/Handoff section per the finding's request, all still hold exactly as written: `ruff check` 48/48 on both branch and pristine master (net zero new); `uv run pytest -q -k applications` → `7 passed, 195 deselected`; `uv run pytest -q -k test_gdap_role_map` → `4 passed`; `grep -rnP '[\x{4e00}-\x{9fff}]'` over the five files this ticket touched → no output; `README.md` lines 5-75 diffed byte-for-byte against `vendor-mcp-development/reference/readme-connector-section.md` → identical.

Per `legs/dev.md` S1 "评审返工"/"Review rework": a must-fix I judge not to hold still gets written up with evidence rather than silently dropped or silently overridden. No edit was made to the frozen `docs/tickets/PRD-21582.md` (review rework does not reopen the frozen main doc; corrections for a disputed finding live here). Leaving this for round 2 to judge: either confirm the `547` vs `482/483` measurement-path explanation above resolves it, or point out what in the repro steps above is wrong.

Gates re-run clean otherwise on the current branch tip (`1e522e7`): no new failures beyond the one pre-existing, baseline-red `test_tools_list_snapshot` failure present on pristine `master` too (`toolchain.md`/`REVIEW.md` §3 WARN: "基线即红的遗留失败（与本次改动无关）", unchanged from the original Self-test's own classification of it).
