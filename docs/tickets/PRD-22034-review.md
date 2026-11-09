# PRD-22034 · Code review

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
