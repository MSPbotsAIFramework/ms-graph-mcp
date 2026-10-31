# PRD-21618 · Code review

## Round 1 · 2026-10-31 · reviewed dev/PRD-21618 @ 83590c9 (base 443fe48)

Verdict: changes requested

### Findings

1. [must-fix] src/graph_mcp/tools/service_principals.py:42-46,128-130 — `_parse_graph_datetime(start_date_time)` calls `datetime.fromisoformat(value.replace("Z", "+00:00"))` on a caller-supplied `start_date_time` with no exception handling around it, and the call site at line 128-130 is outside the `try`/`except GraphError` block (lines 101/157) that wraps the rest of the tool. A malformed or non-ISO `start_date_time` (e.g. `"not-a-date"`, or any string `fromisoformat` rejects) raises a raw `ValueError` that propagates out of the tool call instead of returning the connector's structured error envelope.
   Reproduced directly against this branch's code: calling the tool with `app_id="app-1", start_date_time="not-a-date"` raises `ToolError: Error executing tool graph_service_principal_create_and_add_password: Invalid isoformat string: 'not-a-date'` — not a `{"error": {...}}` envelope.
   This breaks AC5's own stated contract ("not a crash and not a silently-empty success") for a different input than the one AC5 names (`app_id`), but the same principle applies: every other error path in this tool (and every other tool in this connector) returns a structured envelope via `GraphError.to_envelope()` or `error_envelope(...)`; this is the one path that doesn't. It's also a regression relative to the design's own cited precedent, `graph_create_tap` (`users.py:875-937`): that tool never parses `start_date_time` locally — it passes the string straight through to Graph as `startDateTime` and lets Graph's own 400 response (classified by `api_client.py`) surface as the `invalid_argument` envelope. This tool *has* to parse the date locally (Tech design §"Change list": there's no native `lifetimeInMinutes` field for `addPassword`, so `end_date_time` must be computed client-side), and that necessary addition introduced an unhandled-exception surface that wasn't present in the tool it's modeled on. No AC/TC exercises this path, so none of the 8 passing unit tests catch it.
   Fix: wrap the `_parse_graph_datetime(start_date_time)` call in a `try`/`except ValueError` (or move it inside the existing `try` block and catch `ValueError` alongside `GraphError`) and return `error_envelope("invalid_argument", f"start_date_time is not a valid ISO 8601 date-time: {start_date_time!r}", False)` instead of letting it propagate.

### Fixes

(to be filled in by the dev leg on rework)
