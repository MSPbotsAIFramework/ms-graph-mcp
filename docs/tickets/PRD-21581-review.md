# PRD-21581 · Code review

## Round 1 · 2026-11-05 · reviewed dev/PRD-21581 @ 6da7918 (base master @ 080f4ef)

Verdict: approved

### Findings

No must-fix found. Two suggestions, neither blocking:

1. [suggestion] `src/graph_mcp/server.py:71-82` — the `instructions=` string lists the existing tool domains by name but was not extended with a short phrase for the new `policies` domain. The tech design itself called this "optional, nice-to-have, not required by any test" (`docs/tickets/PRD-21581.md` Change list), and `test_service_instructions_present_and_bounded` still passes. Not required; a future ticket touching that string can fold it in.
2. [suggestion] `docs/gdap-role-map.yaml` — the `Security Reader` role for `graph_get_security_defaults_policy` is explicitly flagged as unverified (Open Question Q1 in the design doc). This is documentation-only and does not gate the tool's runtime behavior (gated by Graph's own `Policy.Read.All`), so it is correctly not a must-fix — flagging here only so the note is not lost if this ticket's `-review.md` is read in isolation later.

### Independent verification performed

- `uv run pytest -q` on `dev/PRD-21581 @ 6da7918`: **1 failed, 221 passed** — matches the Self-test section exactly.
- Same command on pristine `master @ 080f4ef` (read-only worktree): **1 failed, 215 passed**, same single failure (`test_tools_list_snapshot` / `graph_list_user_groups: description too long`). Confirms 0 new failures and +6 new tests, and that the one failure pre-dates this ticket (not introduced by this diff or by the merge).
- `uvx ruff check .`: 48 errors on `dev/PRD-21581`, 48 errors on pristine `master` — net zero new lint findings, matches Self-test.
- `grep -rnP '[\x{4e00}-\x{9fff}]' --exclude-dir=.git --exclude-dir=.venv src/ tests/ README.md docs/gdap-role-map.yaml`: no output (the two hits the Self-test section flags are only in the ticket's own frozen `docs/tickets/PRD-21581.md`, which is documentation, not connector surface).
- README `## MSPbots Connector` block (`README.md` lines 5-75) diffed byte-for-byte against `~/.claude/skills/vendor-mcp-development/reference/readme-connector-section.md`: exact match.
- Cross-checked tool-count consistency independently of the repo's own test: `tests/test_tools.py`'s `EXPECTED_TOOLS` has 50 entries including the new tool; `docs/gdap-role-map.yaml` has 50 top-level keys including the new tool; `README.md` Tools table has 50 `graph_*` rows; Overview sentence says "It exposes 50 tools". All four agree.
- Confirmed the four other tickets merged into `master` ahead of this branch (PRD-21580 `graph_list_named_locations`, PRD-21578 `graph_delete_message`, PRD-21582 `graph_list_applications`, PRD-21618 `graph_service_principal_create_and_add_password`) are all still present in README and the diff after the dev leg's merge commit `c4cccf7` — nothing was dropped by the conflict resolution.
- `src/graph_mcp/tools/policies.py` diffed against `src/graph_mcp/tools/domains.py` (the design's stated model): same import shape, same `register()` signature, same `NO_TOKEN` / `GraphError` / `dump_json_capped` reuse, no new abstractions, no new third-party dependency.
- `src/graph_mcp/api_client.py`: no logging calls of any kind — confirms the token is never written to a log, consistent with the Self-test's security claim.
- `gitleaks` was not available in this review environment (binary not installed); relying on the dev leg's own Self-test finding (one pre-existing, unrelated `key_id` GUID match in a different ticket's frozen doc, not touched by this diff) since the diff itself adds no new string literals resembling secrets.

### Standards checked

- Credentials read only from the per-request `X-Ms-Graph-Token` header via the existing `client_factory()` / `contextvars` mechanism; no new state shared across requests (`server.py`'s `GatewayTokenMiddleware`, unchanged).
- Tool name/parameters/return/errors consistent with the tech design; errors are the connector's standard structured envelope via `GraphError.to_envelope()`.
- Tests updated alongside the new tool (6 new cases, `tests/test_tools.py`); Self-test shows the tests actually run (`-k security_defaults_policy -> 6 passed`), re-verified independently above.
- README Connector section byte-matches the reference (see above); no Chinese-language content introduced.
- No cross-repo header/field added (`mcp-track.md` §1.2 does not apply — single repo, no platform counterpart).
- SOP §14 checklist: additive-only change, no new dependency, no write capability added, stateless.

### Scope

Diff is confined to: `src/graph_mcp/tools/policies.py` (new), `src/graph_mcp/server.py` (import + registration), `README.md` (count + one table row + one Known Gaps bullet), `docs/gdap-role-map.yaml` (one new entry), `tests/test_tools.py` and `tests/test_gdap_role_map.py` (new tests + count bumps), plus the ticket's own `docs/tickets/PRD-21581.md` / `.ac.json`. No existing tool's behavior changed. Matches the tech design's Change list exactly.

Status: frozen @ 6da7918
