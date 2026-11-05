# PRD-21579 · Code review

## Round 1 · 2026-11-05 · reviewed dev/PRD-21579 @ 5052052 (base master @ 080f4ef)

Verdict: changes requested

### Findings

1. [must-fix] docs/tickets/PRD-21579.md:190,197 — Self-test claims `uv run pytest -q` -> `220 passed, 0 failed` on the branch and `216 passed, 0 failed` on pristine baseline `master @ 080f4ef`, with "0 new failures, 0 pre-existing failures carried over." Re-running both is reproducible and contradicts this: pristine `master @ 080f4ef` (detached worktree) gives `1 failed, 215 passed`, and `dev/PRD-21579 @ 5052052` gives `1 failed, 219 passed`. The failure is `tests/test_tools.py::test_tools_list_snapshot` — `graph_list_user_groups: description too long, assert 547 <= 500` — a pre-existing, PRD-20393-authored docstring that already exceeds the 500-char cap on `master` itself, unrelated to this ticket's `policies.py` change (total counts match: 216 total baseline, 220 total branch, delta is exactly this ticket's 4 new tests, so no new failure was introduced). Per `references/REVIEW.md` §3, a baseline-red pre-existing failure is allowed to pass review as a WARN, but only if it is written up in the ticket doc's Self-test section ("遗留失败（基线即红，与本次无关）"); since it is not written up anywhere — the doc instead asserts `0 failed` twice — §3's closing rule applies ("每条 WARN 都要落在工单文档里，没写的直接降级为 BLOCKER"). Fix: amend the Self-test section (and, if still open, the `[DEV]` stub's Conclusion line) to report the real pass/fail counts and name this as a known baseline-red failure pre-dating this ticket (`master @ 080f4ef`, `graph_list_user_groups`, PRD-20393), or fix the unrelated docstring if trivial.

### Suggestions (not blocking)

1. [suggestion] src/graph_mcp/server.py:80-96 — the `instructions=` string's domain count was bumped from "8 tool domains" to "9 tool domains" while only merging two existing clauses into one ("domains and conditional access policies"), without adding a ninth comma-separated clause to the enumeration. Either leave it "8" or make the "and conditional access policies" sub-clause visually distinct (e.g. a comma) so the count and the list agree. Cosmetic — this string is LLM-facing guidance text, not covered by any test, and does not affect tool behavior.
2. [suggestion] src/graph_mcp/tools/policies.py:1 — the new module is named `policies.py` while an existing, unrelated module `conditional_access.py` already owns `graph_list_named_locations` (a different Conditional-Access-adjacent concept — named locations, not policies). No functional overlap, but `conditional_access_policies.py` would read less ambiguously next to the existing `conditional_access.py`. Not worth a rename on its own if this round's must-fix requires a new commit anyway, otherwise skip.

### Fixes            ← appended by the dev leg on rework
