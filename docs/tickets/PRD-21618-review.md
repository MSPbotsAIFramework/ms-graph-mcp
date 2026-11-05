# PRD-21618 · Code review

Status: frozen @ ae004c2

## Round 1 · 2026-10-31 · reviewed dev/PRD-21618 @ 83590c9 (base 443fe48)

Verdict: changes requested

### Findings

1. [must-fix] src/graph_mcp/tools/service_principals.py:42-46,128-130 — `_parse_graph_datetime(start_date_time)` calls `datetime.fromisoformat(value.replace("Z", "+00:00"))` on a caller-supplied `start_date_time` with no exception handling around it, and the call site at line 128-130 is outside the `try`/`except GraphError` block (lines 101/157) that wraps the rest of the tool. A malformed or non-ISO `start_date_time` (e.g. `"not-a-date"`, or any string `fromisoformat` rejects) raises a raw `ValueError` that propagates out of the tool call instead of returning the connector's structured error envelope.
   Reproduced directly against this branch's code: calling the tool with `app_id="app-1", start_date_time="not-a-date"` raises `ToolError: Error executing tool graph_service_principal_create_and_add_password: Invalid isoformat string: 'not-a-date'` — not a `{"error": {...}}` envelope.
   This breaks AC5's own stated contract ("not a crash and not a silently-empty success") for a different input than the one AC5 names (`app_id`), but the same principle applies: every other error path in this tool (and every other tool in this connector) returns a structured envelope via `GraphError.to_envelope()` or `error_envelope(...)`; this is the one path that doesn't. It's also a regression relative to the design's own cited precedent, `graph_create_tap` (`users.py:875-937`): that tool never parses `start_date_time` locally — it passes the string straight through to Graph as `startDateTime` and lets Graph's own 400 response (classified by `api_client.py`) surface as the `invalid_argument` envelope. This tool *has* to parse the date locally (Tech design §"Change list": there's no native `lifetimeInMinutes` field for `addPassword`, so `end_date_time` must be computed client-side), and that necessary addition introduced an unhandled-exception surface that wasn't present in the tool it's modeled on. No AC/TC exercises this path, so none of the 8 passing unit tests catch it.
   Fix: wrap the `_parse_graph_datetime(start_date_time)` call in a `try`/`except ValueError` (or move it inside the existing `try` block and catch `ValueError` alongside `GraphError`) and return `error_envelope("invalid_argument", f"start_date_time is not a valid ISO 8601 date-time: {start_date_time!r}", False)` instead of letting it propagate.

### Fixes

1. [must-fix #1] Fixed in `src/graph_mcp/tools/service_principals.py` (lines around 128-137). `_parse_graph_datetime(start_date_time)` is now called inside a local `try`/`except ValueError` guard: on a parse failure it returns `error_envelope("invalid_argument", f"start_date_time is not a valid ISO 8601 date-time: {start_date_time!r}", False)` immediately, exactly as the finding's suggested fix specified, instead of letting the `ValueError` propagate out of the tool call. The `datetime.now(UTC)` default path (no `start_date_time` given) is unchanged.

   Added a regression test, `tests/test_tools.py::test_sp_create_and_add_password_invalid_start_date_time_returns_structured_error` (also recorded as `TC11` with `"source": "dev"` in `docs/tickets/PRD-21618.ac.json`, since it covers an edge case the original AC/TC set didn't name): calls the tool with `start_date_time="not-a-date"` and asserts the result is `{"error": {"code": "invalid_argument", "retryable": false, ...}}` with the bad value quoted in the message, and that `POST .../addPassword` is never reached (the service-principal create step, which happens before date parsing, still runs).

   Verified the fix two ways:
   - **Red on the pre-fix code**: `git stash push -- src/graph_mcp/tools/service_principals.py` (keeping the new test in place) then `uv run pytest -q tests/test_tools.py::test_sp_create_and_add_password_invalid_start_date_time_returns_structured_error` reproduces the exact failure mode the review reported: `ToolError: Error executing tool graph_service_principal_create_and_add_password: Invalid isoformat string: 'not-a-date'`. `git stash pop` restored the fix.
   - **Green on the fixed code**: same test passes in isolation and as part of the full suite.

   Full gate after the fix, run on the branch already synced with `master @ 443fe48` (confirmed current — `git merge-base --is-ancestor origin/master HEAD` passes, no re-sync needed):
   - `uv run pytest -q`: **210 passed, 1 failed** (same pre-existing `test_tools_list_snapshot` / `graph_list_user_groups` description-length failure already documented in the `[DEV]` stub and `TC10`'s evidence — unrelated to this module, reproduces identically on pristine `master`). 210 = the prior 209 + this round's 1 new regression test; 0 new failures.
   - `uvx ruff check`: 48 errors total, identical count to pristine `master`; `grep` for `src/graph_mcp/tools/service_principals.py` and `tests/test_tools.py` in the output returns nothing — 0 new findings in the files this round touched.

   No other code paths were touched; this is the only must-fix listed in Round 1.

## Round 2 · 2026-10-31 · reviewed dev/PRD-21618 @ ae004c2 (base 443fe48)

Verdict: approved

### Round 1 must-fix check

1. [must-fix #1] Confirmed fixed. Re-read `src/graph_mcp/tools/service_principals.py:128-137`: `_parse_graph_datetime(start_date_time)` is now called inside a local `try`/`except ValueError`, returning `error_envelope("invalid_argument", f"start_date_time is not a valid ISO 8601 date-time: {start_date_time!r}", False)` on a parse failure instead of letting the `ValueError` escape — matches the review's suggested fix exactly. The error-envelope shape and the `False` (non-retryable) flag are consistent with the connector's other `invalid_argument`/`service_principal_ambiguous` envelopes in the same file.
   Independently re-verified red/green rather than trusting the Fixes note: checked out the pre-fix (`142a16f`) version of `service_principals.py` into the working tree, re-ran the new test — it fails with the exact reported `ToolError: Error executing tool graph_service_principal_create_and_add_password: Invalid isoformat string: 'not-a-date'`; restored the fixed file (`git status --short` clean afterward) and the test passes again.
   New test `tests/test_tools.py::test_sp_create_and_add_password_invalid_start_date_time_returns_structured_error` asserts `error.code == "invalid_argument"`, `error.retryable is False`, the bad value quoted in the message, and `post_calls == [("/servicePrincipals", {"appId": "app-1"})]` (confirms `addPassword` is never reached once the date fails to parse, while the idempotent find-or-create step still runs) — correctly targets the reported defect, not an implementation detail.

### Diff since Round 1 (`142a16f...ae004c2`)

Only 4 files touched, exactly the fix + its test + the ac.json/review.md bookkeeping: `src/graph_mcp/tools/service_principals.py`, `tests/test_tools.py`, `docs/tickets/PRD-21618.ac.json`, `docs/tickets/PRD-21618-review.md`. No other code paths changed; no scope creep.

### Full gate, re-run independently (not reused from the [DEV] stub)

- `uv sync`: clean, 47 packages, no changes.
- `uv run pytest -q`: 210 passed, 1 failed (`test_tools_list_snapshot` — `graph_list_user_groups` description 547 > 500 chars). Confirmed pre-existing and unrelated: same failure reproduces identically on a separate pristine `master @ 443fe48` worktree. 0 regressions attributable to this ticket.
- `uvx ruff check .`: 48 errors on this branch, 48 errors on pristine `master` — identical count, 0 new findings.
- Chinese-character scan (`grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv .`): hits only inside quoted/cited Chinese text in frozen ticket prose (`docs/tickets/PRD-21618.md`, `docs/tickets/PRD-21676.md` — a different ticket's doc already in this repo), not in source or this ticket's own written prose. No source-code or new-documentation Chinese.
- `README.md`: unchanged since Round 1 (not part of this round's diff); Round 1 did not flag it.

### Findings

No must-fix. No suggestions beyond what Round 1 already covered.

### Conclusion

Round 1's single must-fix is fixed, verified independently (not just re-reading the Fixes note), with no new issues introduced by the fix itself or its regression test. Approved for merge into `master`, INT publish, and connector wiki check (vendor-mcp track, single repo, `Release order: any`).
