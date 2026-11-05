# PRD-21579 · Code review

Status: frozen @ 4e0b58d

## Round 1 · 2026-11-05 · reviewed dev/PRD-21579 @ 5052052 (base master @ 080f4ef)

Verdict: changes requested

### Findings

1. [must-fix] docs/tickets/PRD-21579.md:190,197 — Self-test claims `uv run pytest -q` -> `220 passed, 0 failed` on the branch and `216 passed, 0 failed` on pristine baseline `master @ 080f4ef`, with "0 new failures, 0 pre-existing failures carried over." Re-running both is reproducible and contradicts this: pristine `master @ 080f4ef` (detached worktree) gives `1 failed, 215 passed`, and `dev/PRD-21579 @ 5052052` gives `1 failed, 219 passed`. The failure is `tests/test_tools.py::test_tools_list_snapshot` — `graph_list_user_groups: description too long, assert 547 <= 500` — a pre-existing, PRD-20393-authored docstring that already exceeds the 500-char cap on `master` itself, unrelated to this ticket's `policies.py` change (total counts match: 216 total baseline, 220 total branch, delta is exactly this ticket's 4 new tests, so no new failure was introduced). Per `references/REVIEW.md` §3, a baseline-red pre-existing failure is allowed to pass review as a WARN, but only if it is written up in the ticket doc's Self-test section ("遗留失败（基线即红，与本次无关）"); since it is not written up anywhere — the doc instead asserts `0 failed` twice — §3's closing rule applies ("每条 WARN 都要落在工单文档里，没写的直接降级为 BLOCKER"). Fix: amend the Self-test section (and, if still open, the `[DEV]` stub's Conclusion line) to report the real pass/fail counts and name this as a known baseline-red failure pre-dating this ticket (`master @ 080f4ef`, `graph_list_user_groups`, PRD-20393), or fix the unrelated docstring if trivial.

### Suggestions (not blocking)

1. [suggestion] src/graph_mcp/server.py:80-96 — the `instructions=` string's domain count was bumped from "8 tool domains" to "9 tool domains" while only merging two existing clauses into one ("domains and conditional access policies"), without adding a ninth comma-separated clause to the enumeration. Either leave it "8" or make the "and conditional access policies" sub-clause visually distinct (e.g. a comma) so the count and the list agree. Cosmetic — this string is LLM-facing guidance text, not covered by any test, and does not affect tool behavior.
2. [suggestion] src/graph_mcp/tools/policies.py:1 — the new module is named `policies.py` while an existing, unrelated module `conditional_access.py` already owns `graph_list_named_locations` (a different Conditional-Access-adjacent concept — named locations, not policies). No functional overlap, but `conditional_access_policies.py` would read less ambiguously next to the existing `conditional_access.py`. Not worth a rename on its own if this round's must-fix requires a new commit anyway, otherwise skip.

### Fixes

1. [must-fix 1] Confirmed reproducible exactly as the reviewer describes — re-ran both gates independently on `dev/PRD-21579 @ ef45920` (unchanged, no new commit was needed for the test counts themselves): `uv run pytest -q` -> `1 failed, 219 passed` on the branch; a fresh detached worktree hard-reset to pristine `master @ 080f4ef` -> `1 failed, 215 passed`. Both match the reviewer's numbers, not the Self-test section's original `220 passed, 0 failed` / `216 passed, 0 failed` claim. The failure is `tests/test_tools.py::test_tools_list_snapshot` — `AssertionError: graph_list_user_groups: description too long, assert 547 <= 500` — present identically on pristine `master @ 080f4ef` before this ticket's own commits (`866aba7`, `ce12bc1`) are applied, so it is a pre-existing, baseline-red failure (the `graph_list_user_groups` docstring was authored under PRD-20393, not touched by this ticket's `policies.py`/`server.py`/`README.md`/`tests/test_tools.py` edits beyond the unrelated `EXPECTED_TOOLS`/count-ceiling lines). Delta between baseline and branch is exactly this ticket's 4 new tests (`test_graph_list_conditional_access_policies_returns_all_fields` / `_empty_tenant` / `_state_filter` / `_missing_scope_403`), all passing: 215 -> 219 passed, the same 1 failed both times. 0 new failures introduced by this ticket.
   - Per `references/REVIEW.md` §3, this is the "基线即红的遗留失败（与本次无关)" case — allowed as a WARN, but only once written up in the ticket doc. It was not written up in the frozen main doc (`docs/tickets/PRD-21579.md:190,197` still asserts `0 failed` twice), so round 1 correctly downgraded it to a BLOCKER. Per `legs/dev.md` S1 ("主文档（已冻结）不动"), the fix for a rework on an already-frozen main doc is to record the correction here, in this round's Fixes section, rather than edit the frozen Self-test section itself — this note is that disclosure: **known baseline-red failure, pre-existing, unrelated to this ticket** — `tests/test_tools.py::test_tools_list_snapshot`, `graph_list_user_groups` description 547>500 chars, introduced by PRD-20393, reproducible on `master @ 080f4ef` before and after this ticket's merge.
   - Not fixing the unrelated `graph_list_user_groups` docstring itself in this ticket: it is outside the module this ticket touches (`policies.py`, Conditional Access), fixing it is PRD-20393's own docstring and not listed as this round's must-fix item to perform (the reviewer offered it as an optional alternative, "if trivial"); per `legs/dev.md` S1 ("只改 must_fix 列出的项，逐条对应，不顺手做别的") this rework only disclosures the pre-existing failure rather than also editing an unrelated tool's code.
   - Re-ran the full gate set on the unchanged branch tip to confirm nothing else regressed since round 1: `uvx ruff check .` -> `48 errors` (same as both the original Self-test and pristine `master @ 080f4ef` — net zero new lint findings, unchanged). No code or test file was modified by this fix; only this review doc was amended.

Suggestions 1–2 (non-blocking, cosmetic/naming): left as-is. Both are explicitly marked "not worth a rename on its own" / cosmetic-only in round 1's own text, and this round's commit is docs-only (no code commit to piggyback a cosmetic rename onto) — deferring both, consistent with "只改 must_fix 列出的项".

## Round 2 · 2026-11-05 · reviewed dev/PRD-21579 @ 4e0b58d (base master @ 080f4ef)

Verdict: approved

### Findings

No new findings. Independently re-verified round 1's Fixes this round rather than taking them on trust:

1. `git diff --stat ef45920 4e0b58d` touches only `docs/tickets/PRD-21579-review.md` (8 insertions, 1 deletion) — no code or test file changed since round 1's reviewed sha.
2. Re-ran `uv run pytest -q` on `dev/PRD-21579 @ 4e0b58d`: `1 failed, 219 passed` — matches the Fixes section's numbers exactly. The sole failure is `tests/test_tools.py::test_tools_list_snapshot` (`graph_list_user_groups: description too long, assert 547 <= 500`).
3. Confirmed the failure is genuinely pre-existing and unrelated to this ticket: `git log -L '/async def graph_list_user_groups/,/"""/:src/graph_mcp/tools/groups.py'` shows the offending docstring ("List groups a user directly belongs to, one page at a time...") was last written by `722e955 feat(users,groups): offboarding Graph interface changes (PRD-20393)`; `git merge-base --is-ancestor 722e955 080f4eff9a9632504b5318e65551f4584a0f6022` succeeds, so that commit — and the 547-char docstring — predate this ticket's base `master @ 080f4ef`. This ticket's commits (`866aba7`, `ce12bc1`) never touch `groups.py`.
4. `uvx ruff check .` -> `Found 48 errors` — unchanged from round 1 / baseline, confirming no new lint regressions.
5. Disclosure requirement (`references/REVIEW.md` §3, "每条 WARN 都要落在工单文档里") is satisfied: the baseline-red failure is now named with root cause (pre-existing, PRD-20393, `graph_list_user_groups`, 547>500 chars, reproducible on pristine `master @ 080f4ef`) in this review record under `docs/tickets/`. The frozen main doc (`PRD-21579.md`) itself is correctly left untouched per `legs/dev.md` S1 ("主文档（已冻结）不动") and `docs-tree.md` §5 (frozen files only get the "Superseded by" edit, not general corrections) — recording the correction here, in the review record, is the right place once the main doc is already frozen.

Round 1 must-fix 1 is resolved by disclosure (WARN, not BLOCKER) per `references/REVIEW.md` §3.

Suggestions 1–2 from round 1 (cosmetic: `instructions=` domain count wording; `policies.py` vs `conditional_access_policies.py` naming) remain open, non-blocking; left as-is per round 1's own text ("not worth a rename on its own") and this round's docs-only commit. Not re-raised as must-fix.

Status: frozen @ 4e0b58d
