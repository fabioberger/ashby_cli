from __future__ import annotations

import click

from ._base import json_body_options, run_post


@click.group("file")
def file_group():
    """File endpoints (file.*) — read-only."""


@file_group.command("info")
@click.option("--file-handle", "file_handle", required=True, help="Opaque file handle string.")
@json_body_options
@click.pass_context
def file_info(ctx, file_handle, json_flag, json_file):
    """POST file.info — resolve a file handle into a signed download URL."""
    run_post(ctx, "file.info", json_flag, json_file, {"fileHandle": file_handle})
