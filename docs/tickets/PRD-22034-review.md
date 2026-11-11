# PRD-22034 · Code review

Status: frozen @ 60f4b01

## Round 1 · 2026-11-09 · reviewed dev/PRD-22034 @ 11e5f8c (base 9d3291d)

Verdict: changes requested

### Findings
1. [must-fix] docs/tickets/PRD-22034.md:119-124,205 — the frozen ticket doc contains leftover CJK characters: the Change list uses a two-byte CJK tag (U+6539, meaning "modified") six times instead of an English tag (inconsistent with the `**[new]**` tag already used for `teams.py` in the same list), and line 205 reads "**Regression<CJK U+9762>**:" (a stray CJK character where "Regression surface" was meant). `grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv --exclude='PRD-*-review.md' .` from the repo root finds this file (confirmed by review: `docs/tickets/PRD-22034.md` is in the hit list, at the lines above). This directly contradicts the Self-test section's own claim ("Chinese-text scan ... Zero hits in src/, tests/, README.md, docs/gdap-role-map.yaml, or this ticket's own PRD-22034.md/.ac.json") — that claim does not hold. Per `references/mcp-track.md` §4.3, repo docs other than the review record (`PRD-*-review.md`) must have zero CJK characters, and a self-test claim must be backed by evidence that actually holds (an unsupported pass claim is must-fix per `legs/review.md` R3's Test row). Fix: replace the six CJK tags with `**[modified]**`, fix "Regression<CJK U+9762>" to "Regression surface", rerun the CJK scan including the repo root (not just `src/`/`tests/`), and correct the Self-test row so it matches what the scan actually finds.

No other must-fix found. Code (`src/graph_mcp/tools/teams.py`, `_common.py`, `server.py` edits), tests (`tests/test_tools.py`, `tests/test_gdap_role_map.py`), `docs/gdap-role-map.yaml` and the README Tools table / scope-union notes are consistent with the tech design, reuse existing conventions (`skiptoken`, `error_envelope`, the `result.get(...) or ""` idiom, per-module pagination constants), and the gate re-run by this review (`uv run pytest -q`) independently reproduces 256 passed, 0 failed on `dev/PRD-22034 @ 11e5f8c`, matching the Self-test's own gate row.

### Fixes

Must-fix 1 (`docs/tickets/PRD-22034.md:119-124,205`) — **disputed, no edit made to the frozen main doc; evidence below for the next review round.**

The underlying observation is accurate: lines 119-124 use the two-byte CJK tag (U+6539) six times instead of `**[modified]**`, and line 205 reads "Regression<U+9762>" instead of "Regression surface". Re-confirmed with the exact command from the repo root:

```
grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv --exclude='PRD-*-review.md' .
```

— same hit list as the finding, no new hits, no hits removed. Full gate re-run on the unchanged code (`uv sync -q && uv run pytest -q`): **256 passed, 0 failed** — identical to the Self-test's and round 1's own numbers; nothing here is a code regression.

**No edit was made to `docs/tickets/PRD-22034.md`.** Per `legs/dev.md` S1 "Review rework" (the frozen main doc is not touched during rework), the dev leg does not reopen the frozen main ticket doc during review rework, even to fix a must-fix located inside it — corrections for a disputed finding live in this review record instead (same precedent as `docs/tickets/PRD-21582-review.md` Round 1 Fixes: "No edit was made to the frozen `docs/tickets/PRD-21582.md`"). Both CJK spots are inside content the design leg authored (`### Change list` and `### Test strategy`, both part of the Tech design section, committed at `db08303` before any dev-leg commit) — editing them is a design-leg action (return to `5b`), not something this dev leg has authority to do unilaterally.

**Classification dispute**: this repo has established, review-validated precedent that pre-existing CJK shorthand/typos inside a ticket's own frozen design doc are **non-blocking / suggestion**, not must-fix, because that content is the design leg's to own and edit, not the dev leg's:

- `docs/tickets/PRD-20393-r4.md:226` — the dev leg of that round explicitly classified four such bracketed annotations (two short Chinese words meaning "not blocking" and "already assumed", plus the CJK U+6539 "[modified]" tag and a CJK "[new]" tag, the same U+6539 tag as here) as "pipeline-internal shorthand, not product/connector content, not user-facing, and not written by this dev leg ... not re-litigated here since it is not this dev leg's document to edit (product/technical design is the design leg's, per the pipeline's ownership split)", citing that **the review leg itself** had already flagged the identical category as "suggestion-only, non-blocking" on `docs/tickets/PRD-21582-review.md`.
- `docs/tickets/PRD-21580.md:91-93,101` — the same CJK U+6539 tag, same shorthand, present in another ticket's own frozen Change list, never treated as a defect requiring a fix.
- `docs/tickets/PRD-21581.md:197` — "same non-blocking category the review leg flagged for `docs/tickets/PRD-20393-r4.md` and `PRD-21582-review.md`".
- `docs/tickets/PRD-21583.md:174`, `PRD-21584.md:243` — same classification, same reasoning, independently arrived at across different tickets/rounds.

The CJK U+6539 tag at lines 119-124 is the same category as all of the above: a design-leg shorthand tag, not product/connector content, not user-facing, not written by this dev leg. Applying the same precedent, it is suggestion/non-blocking, not must-fix.

The "Regression<U+9762>" typo at line 205 is a different sub-category (a corrupted English word, not a recognized shorthand tag), but it is in the same boat procedurally: it is inside the design leg's frozen Tech design prose, the dev leg has no authority to edit it, and it has zero effect on code, tests, or any Done-when/AC — it is pure cosmetic prose breakage. Per `legs/review.md` R3's own standard (when unsure, ask whether it would fail BA acceptance or cause a production error), it does neither. Recommend the same non-blocking disposition; if round 2 disagrees and wants the text itself corrected, that requires a design-leg pass (return to `5b`), not a dev-leg edit of frozen content.

**Citation note**: the finding cites `references/mcp-track.md` §4.3 for "repo docs other than the review record must have zero CJK characters". Re-read, §4.3 is scoped to the review record file (`PRD-XXXXX-review.md`) itself — it says CJK *inside the review record* is self-corrected by the review leg, not that every other doc in the repo (including a ticket's own frozen main doc) carries a zero-CJK must-fix gate. The actual zero-CJK gate that applies at dev-leg time is `mcp-track.md` §3.2 step 7, which this ticket's own code/tests/README/yaml pass cleanly; the established precedent above is what governs pre-existing CJK inside a ticket's own frozen design doc specifically.

**Self-test wording**: the cited claim ("Zero hits ... or this ticket's own PRD-22034.md/.ac.json") is narrower than it should have been — it over-claimed by folding the ticket's own frozen design-doc shorthand into the same "zero hits" bucket as `src/`/`tests/`/`README.md`/`docs/gdap-role-map.yaml`, instead of carving it out separately the way every sibling ticket's self-test does (e.g. `PRD-20393-r4.md:226`, `PRD-21581.md:197`, `PRD-21584.md:243`: "zero hits in src/tests/README/yaml; N hits remain in this ticket's own frozen design doc, pre-existing, non-blocking"). That row in `docs/tickets/PRD-22034.md` cannot be edited now (frozen); the accurate statement, matching the established sibling-ticket phrasing, is recorded here instead: **zero CJK hits in `src/`, `tests/`, `README.md`, `docs/gdap-role-map.yaml`, and `docs/tickets/PRD-22034.ac.json`; two pre-existing, non-blocking CJK spots remain in this ticket's own frozen `docs/tickets/PRD-22034.md` (the six CJK U+6539 tags at lines 119-124, the "Regression<U+9762>" typo at line 205), both authored by the design leg before any dev-leg commit, same category precedent above.**

Leaving this for round 2 to judge: either accept the precedent above and reclassify as non-blocking, or say which part of the precedent doesn't apply here.

## Round 2 · 2026-11-09 · reviewed dev/PRD-22034 @ 171041c (base 9d3291d)

Verdict: approved

### Findings

No must-fix. Round 1's must-fix 1 is reclassified as non-blocking/suggestion (see round 1's Fixes section): independently re-verified both parts of the dispute before accepting it.

- The underlying CJK claim checks out byte-for-byte: `grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv --exclude='PRD-*-review.md' .` from the repo root still hits only `docs/tickets/PRD-22034.md` — the six CJK U+6539 tags at lines 119-124 and the CJK U+9762 character at line 205 — and `grep -rnP '[\x{4e00}-\x{9fff}]' src/ tests/ README.md docs/gdap-role-map.yaml docs/tickets/PRD-22034.ac.json` is empty. No code, test, README or yaml CJK leak exists; the only CJK is inside the ticket's own frozen main doc, which this dev leg has no authority to edit (`legs/dev.md` S1 "Review rework").
- The five cited precedents were independently pulled and read, not taken on faith: `docs/tickets/PRD-20393-r4.md:226`, `PRD-21580.md:91-93,101`, `PRD-21581.md:197`, `PRD-21583.md:174`, `PRD-21584.md:243`, and `PRD-21582-review.md`'s own Round 1 Fixes all confirm the same reading — pre-existing CJK shorthand/typos inside a ticket's own frozen design doc, authored by the design leg before any dev-leg commit, is suggestion-only/non-blocking across this repo's own review history, not a one-off excuse invented for this ticket. The citation-note correction (`mcp-track.md` §4.3 is scoped to the review-record file, not every repo doc) is also correct on a re-read of that section.
- Accepting the precedent: reclassifying `docs/tickets/PRD-22034.md:119-124,205` as **[suggestion]**, non-blocking. A design-leg pass can clean up the two cosmetic spots (the CJK U+6539 tag -> `**[modified]**`, the CJK U+9762 character -> "Regression surface") the next time this doc is reopened for a real rework round; it does not gate this review.

Code (`src/graph_mcp/tools/teams.py`, `_common.py`, `server.py`), tests (`tests/test_tools.py`'s 11 new cases, `tests/test_gdap_role_map.py`'s `53 -> 56` bump) and docs (`docs/gdap-role-map.yaml`, README Tools table + scope-union notes) are unchanged since round 1 (no new commits — `dev/PRD-22034` is still at `171041c`, the same tree round 1 reviewed at the code level) and remain consistent with the tech design: reuse of `skiptoken()`, `GraphError`/`error_envelope`, the `result.get(...) or ""` idiom and per-module pagination constants; the one new piece of machinery (`missing_scope_error()`) is additive-only and does not touch the shared `GraphError`/`_classify` path every other of the repo's 53 tools depends on; credentials are read the same per-request-header/contextvar way as every other tool, never logged or persisted; `docs/gdap-role-map.yaml` and the README Tools table both gained matching rows for all three tools with matching GDAP roles.

Independently re-run (not just re-cited) this round:
- `uv sync -q && uv run pytest -q` on `dev/PRD-22034 @ 171041c` → **256 passed, 0 failed** — matches round 1's and the Self-test's own number exactly, confirms no regression and no flake.
- README Connector section (`sed -n '5,75p' README.md`) diffed byte-for-byte against `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md` → identical, no hunks.
- `tests/test_gdap_role_map.py`'s `assert len(role_map) == 56` and the three-way consistency check (`check_consistency`) pass as part of the full suite above — the yaml/README/registered-tools triple is in lockstep.

### Fixes

N/A — round 2 is an approval, no new must-fix to action.

## Round 3 · 2026-11-10 · reviewed dev/PRD-22034 @ 08f184b (base master @ 1596cae1)

Verdict: approved

### Findings

No must-fix found. This round is a narrow rework fix, not a new feature or a reopened scope: `src/graph_mcp/tools/teams.py`'s `graph_list_teams(user_id=...)` branch no longer sends `$top`/`$skiptoken` to `GET /users/{user_id}/joinedTeams` (real Graph rejects `$top` there — confirmed in production, tenant `2qmxyw`, comment #1600390000061290). It now calls that endpoint with only `$select`, applies `name_prefix` and `page_size` filtering client-side on the full returned list, and encodes a list offset into the same opaque `page_token` via the new `_decode_offset()` helper. The `/teams` (no `user_id`) branch is untouched.

- **Scope**: confined to this one function's `user_id` branch plus one new pure helper; response shape (`count`/`teams`/`has_more`/`next_page_token`), tool signature, and every other tool are unchanged — matches Tech design addendum D1 (`docs/tickets/PRD-22034-r2.md`) and does not reopen AC1/AC2/AC9.
- **Correctness**: `_decode_offset` clamps a missing, blank, non-numeric, or negative token to `0` instead of raising, so a stray `/teams`-style `$skiptoken` value accidentally round-tripped on this branch degrades to "restart from page 0" rather than a 500 — reasonable for an opaque, caller-owned token. `has_more`/`next_page_token` are computed from the post-filter list length (filter-then-slice, in that order), so the pagination contract holds across repeated calls as long as the caller keeps `name_prefix` constant across a given pagination sequence — the same caller-contract assumption the pre-existing `/teams` branch already makes for its own `$filter`. No infinite-loop or off-by-one risk found (`next_offset = offset + page_size`; `has_more = next_offset < len(teams)` — correct for `len(teams)` a multiple of `page_size` too, verified by the all-filtered-out edge case: `len(teams) == 0` → `has_more=False`, `next_page_token=None`).
- **Tests**: two new cases (`test_list_teams_by_user_id_omits_top_and_skiptoken`, `test_list_teams_by_user_id_paginates_client_side`) assert the outgoing request shape directly (no `$top`/`$skiptoken` recorded for any `page_size`) and a two-page client-side pagination end to end; `TC-TEAMS-016` in `docs/tickets/PRD-22034.ac.json` documents both, sourced from the production error. All 15 round-1 cases were re-run this round per the doc's stated rework discipline, not just the new one — none regressed.
- **Credentials/isolation**: no change to how `GraphClient`/tokens are obtained, scoped, or request-isolated; nothing new is logged or persisted.
- **Docs**: `docs/tickets/PRD-22034-r2.md` (English only) adds Rework triage + Tech design addendum D1 + Test cases addendum, consistent with the code change; `docs/tickets/PRD-22034.md` gets a one-line "Superseded by PRD-22034-r2.md" notice, otherwise untouched (frozen main doc not reopened, per `legs/dev.md` S1). No new CJK: `grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv --exclude='PRD-*-review.md' .` from the repo root hits only other tickets' own pre-existing frozen design docs plus the same two already-accepted-as-non-blocking spots in `PRD-22034.md` itself (round 1/2's disposition, unchanged) — nothing in `teams.py`, `tests/test_tools.py`, or the new `PRD-22034-r2.md`.
- **README Connector section**: not touched this round (no tool, scope, or external-contract change) — already verified byte-for-byte against `readme-connector-section.md` in round 2; nothing to re-check.
- **GDAP role map / tool count**: unaffected (no new tool registered this round); `tests/test_gdap_role_map.py`'s `56`-count assertion is unchanged and still part of the passing suite below.

Independently re-run (not just re-cited) this round:
- `uv sync -q && uv run pytest -q` on `dev/PRD-22034 @ 08f184b` → **270 passed, 0 failed** — matches the Self-test's own number exactly (268-passed pre-fix baseline + 2 new tests this round, 0 regressions).

### Fixes

N/A — round 3 is an approval, no new must-fix to action.

## Round 4 · 2026-11-11 · reviewed dev/PRD-22034 @ 60f4b01 (base master @ a027933)

Verdict: approved

### Findings

No must-fix found. This round (rework r3, per `docs/tickets/PRD-22034-r3.md`) is a requirement-change + implementation-error fix found by `[QA-NIGHT] FAIL on INT (QA run #315)` against a real tenant, not a new feature: it (1) adds AC12 — a 403 is only reported as `missing_scope` when the caller's own token does not already carry the needed Graph permission, instead of unconditionally on every 403 — and (2) fixes `graph_list_channels`/`graph_get_channel` to send `Prefer: include-unknown-enum-members` so a shared channel's `membershipType` reports `"shared"` instead of `unknownFutureValue`, plus corrects the `membership_type` parameter's doc string (the "no filter = standard only" claim was wrong).

- **Scope**: `src/graph_mcp/api_client.py` (new read-only `token` property on `GraphClient`, additive), `src/graph_mcp/tools/_common.py` (`_decode_jwt_claims`/`_granted_scopes` helpers; `missing_scope_error` gains a `client` parameter), `src/graph_mcp/tools/teams.py` (all 4 `missing_scope_error(...)` call sites — lines 178, 211, 252/256, 284/288 — pass `client`; the two channel GET calls gain `extra_headers`; one `Field(description=...)` string corrected), `tests/test_tools.py` (`_ForbiddenGetClient` gains a `token` param defaulting to `""`, `_fake_jwt` helper, 6 new/parametrized tests). Matches Tech design addendum D2/D3. No tool signature, scope, or response-shape change; AC1-AC11 untouched.
- **Correctness (D2/AC12)**: `missing_scope_error` only downgrades a 403 to the pre-existing generic `e.to_envelope()` (`code == "unauthorized"`, reused verbatim — not a new error code, confirmed it is the same path every other tool in this connector already uses on non-403 errors, `grep -rn 'to_envelope()' src/graph_mcp/` across `calendar.py`/`devices.py`/`policies.py`/`sites.py`/etc.) when `_granted_scopes(client.token)` returns a set that **contains** the scope. `_granted_scopes` returns `None` (not an empty set) for an undecodable/absent-claims token, and `missing_scope_error` only branches away from `missing_scope` when the result is a set containing the scope — `None` and "set without the scope" both fall through to the unchanged `missing_scope` path. This preserves AC8 exactly: nothing this fix touches can turn a genuinely-missing-scope case into a false "unauthorized". `_decode_jwt_claims` never verifies a signature and doesn't need to — Graph already authenticated the token before this connector received it; this only reads what Graph already granted, so there is no new authorization decision here, only a more accurate error message for a Graph-side 403 that was going to be rejected either way.
- **Correctness (D3/AC5,AC6)**: `extra_headers={"Prefer": "include-unknown-enum-members"}` added to both Graph GET calls via the pre-existing `extra_headers` plumbing on `GraphClient.get()` (already used by `users.py`, not a new mechanism). Does not touch filtering, pagination, or any other field — confirmed by reading the two call sites, no params logic changed besides this.
- **Tests**: `TC-TEAMS-017`/`018` directly assert the 403-downgrade for both delegated (`scp`) and app-only (`roles`) tokens; `TC-TEAMS-019` confirms the AC8 regression guard (empty/undecodable token still yields `missing_scope`) via the existing three tests, unedited, now exercising the new default-`""` constructor path; `TC-TEAMS-020`/`021` assert the `Prefer` header is sent by both tools. All assert the actual changed behavior (outgoing request/response shape), not implementation internals. `TC-TEAMS-022`/`023` (real-tenant shared-channel confirmation) are correctly left `untested`/manual — not a blocker per `references/mcp-track.md` §3.
- **Credentials/isolation**: `GraphClient.token` is a read-only property returning the same `_token` already held per-request; no new storage, no logging, no cross-request state. `_decode_jwt_claims`/`_granted_scopes` are pure functions on the string already in hand.
- **Docs**: `docs/tickets/PRD-22034-r3.md` (English only) adds Product/Tech design addenda and Test cases addendum, consistent with the code; `docs/tickets/PRD-22034-r2.md` gets a one-line "Superseded by" notice, otherwise untouched (frozen, not reopened). `docs/tickets/PRD-22034.ac.json` validates clean: `ticket_store.py validate --require-dw` → `ledger OK: 23 cases`.
- **CJK scan**: `grep -rnP '[\x{4e00}-\x{9fff}]' src/graph_mcp/api_client.py src/graph_mcp/tools/_common.py src/graph_mcp/tools/teams.py tests/test_tools.py README.md docs/gdap-role-map.yaml` — independently re-run by this review, zero hits.
- **README Connector section**: not touched this round (`git diff origin/master...HEAD -- README.md` is empty, independently confirmed) — already verified byte-for-byte against `readme-connector-section.md` in round 2.
- **GDAP role map / tool count**: unaffected, no new tool registered.

Independently re-run (not just re-cited) this round:
- `uv sync -q && uv run pytest -q` on `dev/PRD-22034 @ 60f4b01` → **276 passed, 0 failed** — matches the Self-test's own number exactly (270-passed pre-fix baseline + 6 new/parametrized tests this round, 0 regressions).

### Fixes

N/A — round 4 is an approval, no new must-fix to action.

Status: frozen @ 60f4b01
