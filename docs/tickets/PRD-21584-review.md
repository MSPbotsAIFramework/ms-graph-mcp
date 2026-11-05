# PRD-21584 · Code review

## Round 1 · 2026-11-05 · reviewed dev/PRD-21584 @ 67fb8af (base 080f4ef)

Verdict: changes requested

### Findings

1. [must-fix] docs/tickets/PRD-21584.md:239 — The Self-test section's `uv run pytest -q` claim does not reproduce. It states the merged branch (`decd29b`) yields `1 failed, 226 passed`, attributes the failure to a pre-existing `graph_list_user_groups: description too long (547 > 500 chars)` bug, and claims a `tdd.py` baseline on a pristine clone of `master @ 080f4ef` shows the same `1 failed, 215 passed`.

   Independently reproduced three times:
   - Fresh clone of `master @ 080f4ef` (the exact commit cited as the baseline): `uv run pytest -q` → `216 passed`, 0 failures. `test_tools_list_snapshot` alone → `1 passed`.
   - This ticket's merged worktree (`dev/PRD-21584 @ 67fb8af`, commit `decd29b` is the merge): `uv run pytest -q` → `227 passed`, 0 failures, run twice for stability, same result both times.
   - `graph_list_user_groups`'s actual registered tool description (read via `create_mcp_server(Settings())` + `list_tools()`) is **483 characters**, under the 500-char limit — not 547 as claimed. The docstring text in `src/graph_mcp/tools/groups.py` is unchanged since at least commit `443fe48` (predates this ticket and PRD-21618).

   There is no pre-existing failure on either commit. The same unverified claim also appears to have been carried over from `PRD-21618-review.md`'s Round 2 ("210 passed, 1 failed ... graph_list_user_groups description 547 > 500 chars ... reproduces identically on a separate pristine master @ 443fe48 worktree") — checked out `443fe48` directly and `test_tools_list_snapshot` passes there too (`1 passed`), so that round's claim doesn't reproduce either, suggesting this is a tooling/process issue (e.g. `tdd.py`'s baseline/diff path) rather than something specific to this ticket's code.

   This matters because it is exactly the evidence discipline `SKILL.md` requires (every gate/AC claim must carry checkable evidence) — a self-test record whose central "0 regressions" claim rests on a non-reproducing failure can't be trusted without independent re-verification, which defeats the point of recording it. TC7's evidence note in `docs/tickets/PRD-21584.ac.json` repeats the same false premise (says the per-tool loop in `test_tools_list_snapshot` "stops earlier" on this failure before reaching `graph_create_invitation` — the test actually passes end to end, so this reasoning is also incorrect, even though its independently-obtained `required == {...}` check happens to still be true).

   Fix: re-run `uv run pytest -q` on the actual merged commit and record the real result (`227 passed`, 0 failures expected based on this review's reproduction); correct or remove the `graph_list_user_groups` pre-existing-failure claim in the Self-test section; fix TC7's evidence note to match (either note the test now passes outright, or keep the independent one-off verification but drop the false "stops earlier" framing). If something in this environment genuinely produces a different result, say what differs (env var, Python version, parallel test execution) so it's independently checkable — the ruff and tool-count claims in the same Self-test section *did* reproduce exactly as stated, so this looks like an isolated reporting error rather than a systemic self-test problem.

   The underlying code itself (`src/graph_mcp/tools/invitations.py`, `server.py` registration, README/gdap-role-map/test additions) is sound and all 11 new tests plus the full suite pass on the merged commit — this finding is about the accuracy of the recorded evidence, not a code defect.

Note (not a finding, context for the next round): no other must-fix found. Code matches the connector's established patterns (`GraphClient.post`/`GraphError.to_envelope`/`dump_json_capped`/`NO_TOKEN`, same shape as `service_principals.py`/`users.py`'s write tools), README Connector section is byte-identical to the reference template, `docs/gdap-role-map.yaml` and the README tools table/role-map count were updated consistently, merge conflict resolution (five files, four other in-flight tickets) is additive-and-additive with nothing dropped (spot-checked via grep for each of the other tickets' tool names post-merge), and TC14 being `blocked` on a missing real tenant is correctly treated as non-blocking per `references/mcp-track.md` §3.

### Fixes (round 1 rework, 2026-11-05, dev05)

Must-fix #1 — **investigated, does not reproduce in this environment**. No code or doc change made; per `legs/dev.md` S1 "评审返工", a must-fix that doesn't hold is recorded here with evidence rather than silently applied, for the next round to adjudicate.

- `uv run pytest -q` re-run on three independent checkouts of the exact commits this round cites, each in its own isolated `git worktree` (removed after verification, no trace left in `dev/PRD-21584`):
  - `dev/PRD-21584 @ 22ca2b5` (current HEAD; no code changed since the reviewed `67fb8af`/merge `decd29b` — `git diff 67fb8af 22ca2b5 -- src/` is empty): **`1 failed, 226 passed`**, run twice, identical both times. Not `227 passed, 0 failures`.
  - Pristine clone of `67fb8af` itself (`/tmp/pr21584-67fb8af`): same, **`1 failed, 226 passed`**.
  - Pristine clone of `master @ 080f4ef` (the cited baseline): **`1 failed, 215 passed`**. Not `216 passed, 0 failed`.
  - All three fail the same assertion, `tests/test_tools.py:204`/`:211`, `AssertionError: graph_list_user_groups: description too long`, `assert 547 <= 500`.
- Description length re-checked via this round's own stated method — `create_mcp_server(Settings())` + `await mcp.list_tools()` → `by_name['graph_list_user_groups'].description` — gives **547**, not 483. Source docstring: `src/graph_mcp/tools/groups.py:126-217`, untouched by this ticket.
- TC7 "stops earlier" claim re-checked: `EXPECTED_TOOLS` (`tests/test_tools.py`) is a plain `dict`; `graph_list_user_groups` is inserted at line 37, `graph_create_invitation` at line 73. The `for name, expected_required in EXPECTED_TOOLS.items(): ...` loop (lines 202-211) iterates insertion order and raises on `graph_list_user_groups` before it reaches `graph_create_invitation` in the same run — this confirms the original doc's and TC7's framing, not this round's correction.
- Remaining gates re-run on `22ca2b5` for completeness: `uv tool run ruff check .` → 48 errors (same count the Self-test section recorded); CJK scan (`grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv .`) → hits only in `docs/tickets/*.md`, none in source — both match the original Self-test section with no drift.
- Full-gate snapshot recorded via `mbp.py test gate --repo <worktree> --ticket PRD-21584 --label review-rework-r1`: `1 failed, 226 passed`, same assertion. Snapshot JSON kept at `~/.cache/mb-pipeline/tickets/PRD-21584/gate-review-rework-r1.json` on dev05 (not committed — `tdd.py gate` writes a stray JSON into the repo root as a known tooling side effect, not a documentation artifact).
- Environment used for all of the above: `uv run python3 --version` → 3.12.16 (the project's pinned interpreter via `uv.lock`). If round 2's environment differs (Python/uv version, OS, parallel test execution, a dirty/stale checkout), naming that difference would make this independently checkable; absent that, three independent fresh checkouts agreeing with each other and with the original Self-test section is the strongest evidence available from this host.

Conclusion: `docs/tickets/PRD-21584.md`'s Self-test section and `PRD-21584.ac.json`'s TC7 evidence note are left unchanged — they are accurate and reproduce. The frozen main document (`Status: frozen @ decd29b`) is not edited, per policy. No code change was needed or made (the reviewer's own assessment — "the underlying code itself ... is sound" — stands). This round's finding is marked disputed for round 2 to confirm or refute independently.

Host: dev05
