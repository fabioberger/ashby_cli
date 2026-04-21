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
| `interview-schedule` | create • info • list • update • cancel |
| `interview-stage` | info • list |
| `interview-stage-group` | list |
| `interview` | info • list |

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

- **Endpoint coverage** is driven by the 2026 reference inventory (POST-only, `{resource}.{action}`). If Ashby adds new verbs, add a new subcommand in `src/ashby_cli/commands/<resource>.py` — the `_base.run_post` / `run_list` helpers keep it to ~10 lines.
- **Multipart uploads** (`candidate.upload-resume`, `candidate.upload-file`) assume the form field names `resume` and `file`; adjust in `candidate.py::_upload` if Ashby's docs disagree for your org.
- **Field name heuristics** (e.g. `candidateId` vs `id`) match the best info available at build time. Every command accepts `--json` for arbitrary overrides if a flag maps to the wrong body key.
