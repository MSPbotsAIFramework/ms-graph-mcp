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

## Round 2 · 2026-10-31 · reviewed dev/PRD-21582 @ 07b0f58 (base master @ 2e58da7)

Verdict: approved

### Round 1 must-fix re-adjudicated: retracted — root cause was the round-1 reviewer's own uncontrolled Python interpreter, not a defect in the ticket

Round 1 wrongly disputed the original Self-test claim. Round 2's dev rework (the `Fixes` entry above) correctly reproduced `1 failed, 201 passed` and traced the gap to a measurement-path difference, but its proposed mechanism ("FastMCP does not dedent docstrings; round 1 measured a cleaned copy") is not quite right either — `tests/base.py`'s `Tool.from_function` does use the raw `fn.__doc__` unmodified (confirmed by reading `mcp/server/fastmcp/tools/base.py:66` and `server.py`'s `list_tools()`, both pass the docstring straight through with no `cleandoc`/`dedent` call anywhere in the chain). The actual mechanism is one level down, in CPython itself:

- **CPython 3.13 changed how the compiler stores multi-line docstring literals**: as of 3.13, `fn.__doc__` for a multi-line docstring is the compiler's *dedented* text (equivalent to `inspect.cleandoc()`), not the raw source bytes between the triple quotes. On 3.12 and earlier, `fn.__doc__` is the raw literal, indentation and all.
- Verified directly on this exact function (`graph_list_user_groups` in `src/graph_mcp/tools/groups.py`, untouched by this ticket): the raw literal between the `"""` pair in the source is 547 bytes (8-space indentation preserved on 7 continuation lines, confirmed with `cat -A`); `fn.__doc__` read back after `uv run python3` under the interpreter `uv run` picked by default here (3.15.2, since this repo has no `.python-version` and `requires-python = ">=3.12"` has no upper bound) is 483 bytes — dedented.
- Repeated the full gate explicitly pinned to each interpreter uv has installed on this machine:
  - `uv run --python 3.12 pytest -q` → `dev/PRD-21582 @ 07b0f58`: **`1 failed, 201 passed`**; pristine `master @ 2e58da7`: **`1 failed, 194 passed`** — exactly the original Self-test bullet's numbers, and exactly round 2's dispute.
  - `uv run pytest -q` (no `--python`, i.e. whatever uv resolves by default on this machine today, 3.15.2) → branch `202 passed`, master `195 passed` — exactly round 1's numbers.
- **`Dockerfile` pins both build and runtime stages to `python:3.12-slim`.** That is what actually runs on INT/production; 3.12 is therefore the authoritative interpreter for this repo's gates, not whatever a given reviewer's `uv run` happens to resolve to on a machine with multiple Python toolchains installed and no `.python-version` pin.

Conclusion: the original Self-test claim (`1 failed, 201 passed` on the branch, same pre-existing `test_tools_list_snapshot` failure on pristine `master`, introduced by `graph_list_user_groups`'s docstring from an already-merged earlier ticket, unrelated to this ticket's files) was **correct all along**, under the Python version this connector actually ships on. Round 1's must-fix was a false positive caused by round 1 running the gate under an unpinned, newer local interpreter (3.13+) that silently changes docstring-measurement semantics. This is the round-1 reviewer's environment error, not a defect introduced by DEV01's round-1 or round-2 work — no doc or code change was needed, and round 2 was correct not to make one.

**Process note, not a finding against this ticket**: this repo has no `.python-version` file, so `uv run pytest` is non-deterministic across machines/sessions in a way that flips a real assertion (CPython's 3.13 docstring-dedent change). That fragility pre-dates this ticket (the overlong docstring is PRD-21676's, `src/graph_mcp/tools/groups.py` is untouched by this diff) and is out of this ticket's scope to fix. Worth a separate, small follow-up ticket to add a `.python-version` pinned to `3.12` (matching `Dockerfile`) so `uv run` is deterministic for every future ticket's self-test — not filed here since it is not this ticket's code.

### Independent re-verification of the rest of the diff (fresh for round 2, not just re-reading round 1)

- `uv run --python 3.12 pytest -q -k applications` → `7 passed, 195 deselected` (TC1–TC6 + the arithmetic unit test), matches `docs/tickets/PRD-21582.ac.json` evidence exactly.
- `uvx ruff check .`: **48 errors** on `dev/PRD-21582 @ 07b0f58`, **48 errors** on pristine `master @ 2e58da7` — net zero new, confirmed independently (not just re-reading the Self-test claim).
- `grep -rnP '[\x{4e00}-\x{9fff}]'` over every file this ticket's diff touches (`src/graph_mcp/tools/applications.py`, `tests/test_tools.py`, `README.md`, `docs/gdap-role-map.yaml`, `docs/tickets/PRD-21582.md`, `docs/tickets/PRD-21582.ac.json`) → no output; clean.
  - [suggestion] `docs/tickets/PRD-21582-review.md` (this file, added by round 1/round 2's own review rework, not part of the ticket's product diff) quotes a few Chinese phrases verbatim when citing this pipeline's own internal skill docs (`legs/dev.md`'s section name "评审返工", `REVIEW.md` §3's row text). Not product/connector content and not user-facing, so not a must-fix, but future rounds should paraphrase or cite by section number instead of pasting the literal Chinese title, to keep the repo's "no CJK" grep meaningfully zero rather than needing a mental carve-out.
- Live smoke test (`uv run --python 3.12 python -m graph_mcp`, port 8080 per `.env.example`): `/health` → `200`; `POST /mcp` `initialize` with no `X-Ms-Graph-Token` header → `401`; with a placeholder token → `200`, session established, `tools/list` includes `graph_list_applications`.
- README connector boilerplate (`README.md` lines 5–75) diffed byte-for-byte against `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md` → identical (confirmed independently, not re-reading the claim).
- Code read (`src/graph_mcp/tools/applications.py`, `src/graph_mcp/server.py` diff): follows the existing `users.py`/`groups.py`/`domains.py` conventions exactly — `client_factory()` / `NO_TOKEN` credential pattern (no token read from anywhere but the per-request header, nothing persisted, nothing logged), `_DEFAULT_MAX_RESULTS`/`_HARD_CAP_MAX_RESULTS`/`_GRAPH_TOP_MAX` pagination ceiling identical in shape to `groups.py`'s, `skiptoken()`/`dump_json_capped()` reused rather than reimplemented, `GraphError.to_envelope()` for the error path (shared, generically tested elsewhere — a tool-specific 401 test is not this repo's convention, see the existing `graph_list_named_locations` test as the one precedent, and even that is the exception not the rule). No secret *value* is ever returned — Graph's `passwordCredentials` itself never carries the secret, only `keyId`/`displayName`/dates/`hint`, so there is nothing to leak by construction (SOP "运行模型" credential-isolation rule: trivially satisfied, nothing to isolate).
- `docs/gdap-role-map.yaml` / README GDAP role row / `tests/test_gdap_role_map.py` count bump (47→48): consistent, test passes, and the role is explicitly flagged (in both the yaml note and `README.md`'s Known Gaps) as unverified-on-a-real-tenant — correctly not overclaimed.
- Scope documentation (`Application.Read.All`, new permission): README's "Permissions Rollout" note follows the exact same rollout-shape precedent as every prior new-scope tool in this file (re-consent required, returns `unauthorized` until then) — consistent, no shortcuts taken.
- `docs/tickets/PRD-21582.md` merge-conflict writeup (line 239, README/test_tools.py/test_gdap_role_map.py conflicts against PRD-21580/PRD-21578/PRD-21676's already-merged changes): both sides' content kept in full per `toolchain.md` §6 "合并冲突：自己解决"; spot-checked against the actual merged diff — `EXPECTED_TOOLS`/role-map counters were recomputed to the union (48), not either side's pre-merge number; no evidence either side's tool/test was dropped.
- Test coverage (TC1–TC6 in `tests/test_tools.py`): matches `.ac.json` one-to-one, each test asserts the stated behavior (secret-present/no-secret/pagination/GET-only/empty-tenant/expired-secret), no test is asserting implementation details instead of the documented contract.

No new must-fix. No must-fix carried over from round 1 (retracted above, with the dev's dispute vindicated). This review record freezes here.

Status: frozen @ 07b0f58
