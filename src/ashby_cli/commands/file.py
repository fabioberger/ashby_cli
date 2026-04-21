from __future__ import annotations

import click

from ._base import json_body_options, run_post


@click.group("file")
def file_group():
    """File endpoints (file.*)."""


@file_group.command("info")
@click.option("--file-handle", "file_handle", required=True, help="Opaque file handle string.")
@json_body_options
@click.pass_context
def file_info(ctx, file_handle, json_flag, json_file):
    """POST file.info — resolve a file handle into a signed download URL."""
    run_post(ctx, "file.info", json_flag, json_file, {"fileHandle": file_handle})


@file_group.command("create-upload-handle")
@click.option("--context", "context", required=True,
              help="File upload context, e.g. CandidateResume, CandidateFile.")
@click.option("--file-name", "file_name", help="Original filename (optional).")
@click.option("--content-type", "content_type", help="MIME type (optional).")
@json_body_options
@click.pass_context
def file_create_upload_handle(ctx, context, file_name, content_type, json_flag, json_file):
    """POST file.createFileUploadHandle — get a presigned upload URL."""
    run_post(ctx, "file.createFileUploadHandle", json_flag, json_file, {
        "fileUploadContext": context,
        "fileName": file_name,
        "contentType": content_type,
    })
