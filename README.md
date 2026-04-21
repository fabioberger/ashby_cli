# ashby-cli

Agent-friendly command-line wrapper over the [Ashby HQ public API](https://developers.ashbyhq.com/reference/introduction). Every invocation emits a single JSON object on stdout — designed to be called from Claude Skills.

## Install

```bash
cd ashby_cli
pip install -e .
export ASHBY_API_KEY=sk_...
ashby --help
```

Also callable as `python -m ashby_cli ...`.

## Output envelope

All commands emit exactly one line of JSON. Parse with `jq` / `json.loads`, dispatch on `ok`:

```jsonc
// success
{"ok":true,"data":{...},"moreDataAvailable":false,"nextCursor":null,"syncToken":"...","requestId":"..."}

// error (API, network, rate limit, usage)
{"ok":false,"error":{"code":"...","message":"...","httpStatus":200,"requestId":"..."}}
```

### Exit codes
| code | meaning |
|---|---|
| 0 | Success |
| 1 | Ashby API returned `success:false` |
| 2 | CLI usage error (bad flags, unparseable JSON) |
| 3 | Network / timeout / HTTP 5xx |
| 4 | Rate limited (HTTP 429) |

## Supplying request bodies

Three styles, merged with **flag values winning**:

```bash
# 1. Named flags (most common fields exposed)
ashby candidate create --name Alice --email a@example.com

# 2. Inline JSON for nested / uncommon fields
ashby candidate update --id u-1 --json '{"location":{"city":"NYC"}}'

# 3. File or stdin
ashby interview-schedule create --application-id a-1 --json-file events.json
cat events.json | ashby interview-schedule create --application-id a-1 --json-file -
```

## Pagination

`list` commands are **single-page by default**; response echoes `nextCursor` and `syncToken`.

```bash
# page 1
ashby candidate list --limit 100
# page 2 — pass the cursor back
ashby candidate list --limit 100 --cursor <nextCursor>
# or: auto-walk up to --max-pages (default 50)
ashby candidate list --all --max-pages 10
# incremental sync
ashby candidate list --sync-token <syncToken>
```

## Global flags

| flag | default | meaning |
|---|---|---|
| `--api-key` | `$ASHBY_API_KEY` | API key override |
| `--base-url` | `https://api.ashbyhq.com` | API base URL override |
| `--timeout` | `30` | Request timeout (seconds) |
| `--pretty` | off | Indent JSON output |

## Commands

Run `ashby <group> --help` for flags on each command.

| Group | Commands |
|---|---|
| `candidate` | create • info • list • search • update • add-project • remove-project • upload-resume • upload-file |
| `file` | info • create-upload-handle |
| `job` | create • info • list • update • set-status • search |
| `job-posting` | info • list • update |
| `application` | create • info • list • update • change-stage • change-source • transfer • hire • reject • unreject • list-history |
| `interview-event` | list |
| `interview-plan` | list |
| `interview-schedule` | create • list • update • cancel |
| `interview-stage` | info • list |
| `interview-stage-group` | list |
| `interview` | info • list |
| `interviewer-pool` | info • list |

### Resolving interviewer userIds → name/email

Ashby's public API has no `user.*` endpoint, so the only way to turn an interviewer `userId` (as returned by `interviewEvent.list`) into a name or email is via `interviewerPool.info`, whose `qualifiedMembers[]` and `trainees[]` arrays include `{id, firstName, lastName, email, globalRole, isEnabled, isPaused}`. Walk all pools once and build a lookup:

```bash
ashby interviewer-pool list --all --limit 100 \
  | jq -r '.data[].id' \
  | while read pid; do ashby interviewer-pool info --id "$pid"; done \
  | jq -s '[.[] | .data | (.qualifiedMembers // []) + (.trainees // [])] | add | unique_by(.id)'
```

> **Note:** `interviewSchedule.info` does not exist in the Ashby API. To fetch schedule details, combine `interview-schedule list --application-id` with `interview-event list --interview-schedule-id`.

## Usage from Claude Skills

Typical skill snippet (bash):

```bash
resp=$(ashby candidate list --limit 50)
if [ "$(echo "$resp" | jq -r .ok)" = "true" ]; then
  echo "$resp" | jq '.data[] | {id, name}'
else
  echo "$resp" | jq '.error' >&2
  exit 1
fi
```

The CLI never writes free-form text to stdout; stderr is reserved for unexpected crashes (never structured data).

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Tests use [`responses`](https://github.com/getsentry/responses) to mock every HTTP call — no live API key needed. See `tests/test_client.py` and `tests/test_cli.py`.

## Known gaps / calibration notes

- **Read-only endpoints verified live** (2026-04-21) against a real Ashby tenant: every `list` / `info` / `search` command across all groups returns `ok:true` with correct pagination, cursor, and sync-token behaviour. Exit codes (0/1/2/3/4) match the contract.
- **Write endpoints (`create`/`update`/`hire`/`reject`/...) are still untested against live data.** Field-name heuristics may be wrong for some mutation bodies — use `--json` overrides if Ashby rejects a request with `invalid_input`, and please open an issue with the endpoint name.
- **Endpoint coverage:** to add a new Ashby verb, drop a subcommand into `src/ashby_cli/commands/<resource>.py` using `_base.run_post` / `run_list` (~10 lines), then register the group in `commands/__init__.py::ALL_GROUPS`.
- **Multipart uploads** (`candidate.upload-resume`, `candidate.upload-file`) assume form field names `resume` and `file`; adjust in `candidate.py::_upload` if Ashby's docs disagree for your org.
- **`interviewSchedule.info` does not exist** in the Ashby API — don't look for it. Combine `interview-schedule list --application-id` with `interview-event list --interview-schedule-id` to reconstruct schedule details.
- **No public `user.*` endpoint.** Interviewer `userId`s (e.g. from `interviewEvent.interviewerUserIds`) resolve to name/email only via `interviewer-pool info` — see recipe above.
