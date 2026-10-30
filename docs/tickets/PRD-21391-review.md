# PRD-21391 · Code review

## Round 1 · 2026-10-30 · reviewed ms-graph-mcp dev/PRD-21391 @ 059da83 (base master @ 7ccec6f); gdap-mcp dev/PRD-21391 @ a00f649 (base main @ f3528b1)

Verdict: approved

### Scope

Both repos are in Code Repo (Track: vendor-mcp, release order: any, per the `[DESIGN]` stub). Diff taken as `<base>...<dev sha>` in each repo (base = the default branch sha the dev leg last synced against, confirmed current via `git fetch` — neither default branch moved since the dev tick).

- ms-graph-mcp: `src/graph_mcp/tools/users.py`, `docs/gdap-role-map.yaml`, `README.md`, `tests/test_tools.py`, `tests/test_gdap_role_map.py`, `docs/tickets/PRD-21391.{md,ac.json}`.
- gdap-mcp: `app/graph_tools/{users.py,registry.py}`, `docs/gdap-role-map.yaml`, `README.md`, `tests/{fake_microsoft.py,test_flows.py,test_gdap_role_map.py,test_http.py}`.

### Findings

No must-fix found. Two observations, neither rises above `suggestion`:

1. [suggestion] ms-graph-mcp `README.md:79` — the recomputed tool-count line is good practice (matches the ticket's own "Locking regression lessons" section), but the parenthetical explaining the prior drift (39→41→44) is a bit dense for a README reader who isn't this ticket's reviewer. Not required to change.
2. [suggestion] gdap-mcp `app/graph_tools/users.py` — the new tool's docstring repeats the full body comment already present in ms-graph-mcp's copy (expected, per the repo's "copied verbatim" resync convention at `app/graph_tools/__init__.py:1-33`); no action needed, flagging only so a future resync diff isn't surprised by it.

### Verification performed

- `uv run pytest -q` on `ms-graph-mcp dev/PRD-21391 @ 059da83`: **180 passed** (matches the Self-test section's claim; baseline on clean `master` would be 175 — 5 new tests for `graph_list_user_roles`, consistent with TC1/TC3/TC6/TC7/TC8).
- `uv run --frozen pytest -q` on `gdap-mcp dev/PRD-21391 @ a00f649` (real PostgreSQL, `postgres:16-alpine` via `sudo docker run ... -p 127.0.0.1:55432:5432`, per the repo's own README "Local testing" section): **112 passed** (matches the Self-test claim; baseline 110 — 2 new tests, TC2 and TC9).
- `git diff <base>...HEAD -- pyproject.toml uv.lock` empty in both repos — confirms the design's "no new dependency" claim.
- `git diff <base>...HEAD | grep '^\+' | grep -P '[\x{4e00}-\x{9fff}]'` — no match in either repo's diff. (gdap-mcp's repo as a whole does carry pre-existing Chinese comments outside this diff — `.gitignore`, `app/manager_grant.py`, `app/errors.py`, `app/api.py`, `app/main.py`, `app/graph.py`, `app/db.py`, `.env.example`, `pyproject.toml`, `Dockerfile`, `app/exo_tools/registry.py`, etc. — but none of it was touched or added by this ticket, so the Self-test's narrower claim "no Chinese characters introduced" is accurate and this is not a finding against this diff.)
- `sed -n '5,76p' README.md` (ms-graph-mcp) vs `vendor-mcp-development/reference/readme-connector-section.md`: byte-identical modulo one trailing blank line from the `sed` range boundary — not a content difference.
- Read both diffs in full: credentials stay request-scoped (`client_factory()` per call, same pattern as every other tool in both files); no persisted state; tool name/params/response/error shape match the tech design's Data & API contract section exactly; `graph_list_user_roles` issues only `GET` (no PATCH/POST/DELETE in either body); gdap-mcp's copy is verbatim from ms-graph-mcp's body plus the registry opt-in, matching the documented resync convention — no per-tool GDAP plumbing was hand-rolled.
- `docs/gdap-role-map.yaml` has a matching row in both repos, and both repos' `tests/test_gdap_role_map.py` consistency checks were part of the green run above.
- Read `docs/tickets/PRD-21391.ac.json`: 10 cases, TC1-TC9 pass with reproducible evidence strings, TC10 (real-tenant verification) correctly recorded as `blocked` (no real vendor account — not a blocker per `references/mcp-track.md` §3/§7, "missing a real vendor account does not block this track").
- Cross-repo compatibility (`references/mcp-track.md` §1.2): no new request header or field crosses a repo boundary here — both tools are additive, independent endpoints — so the "tolerate missing" rule doesn't apply; `release order: any` in the Handoff section is correct.

### Not applicable to this ticket

- `@mspbots/ui` / UI state coverage — MCP repos have no UI (`references/mcp-track.md` §7a).
- Migration / DROP checks — no schema change in either repo.

Status: frozen @ ms-graph-mcp dev/PRD-21391 059da83, gdap-mcp dev/PRD-21391 a00f649
