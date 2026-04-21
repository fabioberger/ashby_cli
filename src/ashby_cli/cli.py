from __future__ import annotations

import sys

import click

from . import __version__
from .client import AshbyClient, BASE_URL, ClientError, EXIT_USAGE, EXIT_NETWORK, EnvelopeResult
from .commands import ALL_GROUPS
from .output import emit, emit_client_error, set_pretty


CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 120,
}


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=False)
@click.version_option(__version__, prog_name="ashby")
@click.option("--api-key", "api_key", envvar="ASHBY_API_KEY_CLI_OVERRIDE", default=None,
              help="Ashby API key (overrides ASHBY_API_KEY).")
@click.option("--base-url", "base_url", default=BASE_URL, show_default=True,
              help="Override the Ashby API base URL (for testing).")
@click.option("--timeout", type=float, default=30.0, show_default=True,
              help="Request timeout in seconds.")
@click.option("--pretty/--no-pretty", "pretty", default=False,
              help="Pretty-print JSON output (default compact).")
@click.pass_context
def main(ctx: click.Context, api_key, base_url, timeout, pretty) -> None:
    """Agent-friendly command-line wrapper over the Ashby HQ API.

    Every command emits a single JSON object on stdout:

      success: {"ok": true, "data": ..., "moreDataAvailable"?, "nextCursor"?, "syncToken"?}
      error:   {"ok": false, "error": {"code": ..., "message": ..., "httpStatus": ..., "requestId"?}}

    Exit codes:
      0 success
      1 Ashby API error (success=false in envelope)
      2 CLI usage error (bad flags, JSON parse)
      3 Network / timeout / 5xx
      4 Rate limited (HTTP 429)

    Authentication: set ASHBY_API_KEY or pass --api-key.
    """
    set_pretty(pretty)
    ctx.ensure_object(dict)
    ctx.obj["base_url"] = base_url
    ctx.obj["timeout"] = timeout
    ctx.obj["api_key"] = api_key
    ctx.obj["_client"] = None


for group in ALL_GROUPS:
    main.add_command(group)


def main_entry() -> None:
    """Console-script entry that guarantees JSON envelopes on every path (including usage errors)."""
    try:
        main.main(standalone_mode=False)
    except click.UsageError as e:
        msg = e.format_message() if hasattr(e, "format_message") else str(e)
        ctx = getattr(e, "ctx", None)
        cmd_path = ctx.command_path if ctx else ""
        err = {
            "code": "usage",
            "message": f"{cmd_path}: {msg}" if cmd_path else msg,
            "httpStatus": 0,
        }
        emit(EnvelopeResult(ok=False, error=err, exit_code=EXIT_USAGE))
    except click.ClickException as e:
        err = {"code": "click_error", "message": str(e), "httpStatus": 0}
        emit(EnvelopeResult(ok=False, error=err, exit_code=e.exit_code or EXIT_USAGE))
    except ClientError as e:
        emit_client_error(e)
    except click.exceptions.Abort:
        err = {"code": "aborted", "message": "Aborted", "httpStatus": 0}
        emit(EnvelopeResult(ok=False, error=err, exit_code=EXIT_USAGE))
    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover - last-resort safety net
        err = {"code": "internal", "message": f"{type(e).__name__}: {e}", "httpStatus": 0}
        emit(EnvelopeResult(ok=False, error=err, exit_code=EXIT_NETWORK))


if __name__ == "__main__":
    main_entry()
