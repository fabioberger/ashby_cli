# ashby-cli

**Read-only**, agent-friendly command-line wrapper over the [Ashby HQ public API](https://developers.ashbyhq.com/reference/introduction). Every invocation emits a single JSON object on stdout — designed to be called from Claude Skills.

> This CLI intentionally exposes only read endpoints (`list`, `info`, `search`, `listHistory`). No create / update / delete / upload commands. Pair with a read-only Ashby API key to keep blast radius low.

## Install

```bash
cd ashby_cli
pip install -e .
export ASHBY_API_KEY=sk_...   # use a read-only API key
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
# 1. Named flags (most common filters exposed)
ashby candidate search --email a@example.com

# 2. Inline JSON for nested / uncommon fields
ashby application list --json '{"status":"Active"}'

# 3. File or stdin
ashby job list --json-file filters.json
cat filters.json | ashby job list --json-file -
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

Run `ashby <group> --help` for flags on each command. All are read-only.

| Group | Commands |
|---|---|
| `candidate` | info • list • search |
| `file` | info |
| `job` | info • list • search |
| `job-posting` | info • list |
| `application` | info • list • list-history |
| `interview-event` | list |
| `interview-plan` | list |
| `interview-schedule` | list |
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

- **Read-only by design.** Write endpoints (`create`, `update`, `changeStage`, `hire`, `reject`, `uploadResume`, etc.) are intentionally not wrapped. Use the Ashby web UI or a separate tool for mutations — and pair this CLI with a read-only API key.
- **Read-only endpoints verified live** (2026-04-21) against a real Ashby tenant: every `list` / `info` / `search` / `list-history` command returns `ok:true` with correct pagination, cursor, and sync-token behaviour. Exit codes (0/1/2/3/4) match the contract.
- **Adding a new read verb:** drop a subcommand into `src/ashby_cli/commands/<resource>.py` using `_base.run_post` / `run_list` (~10 lines), then register the group in `commands/__init__.py::ALL_GROUPS`.
- **`interviewSchedule.info` does not exist** in the Ashby API — don't look for it. Combine `interview-schedule list --application-id` with `interview-event list --interview-schedule-id` to reconstruct schedule details.
- **No public `user.*` endpoint.** Interviewer `userId`s (e.g. from `interviewEvent.interviewerUserIds`) resolve to name/email only via `interviewer-pool info` — see recipe above.
