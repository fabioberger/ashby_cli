from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def application():
    """Application endpoints (application.*) — read-only."""


@application.command("info")
@click.option("--id", "id_", help="Application UUID (sent as applicationId).")
@click.option("--submitted-form-instance-id", "submitted_form_instance_id")
@click.option("--expand", multiple=True,
              help="Repeatable. Expand related objects (e.g. candidate, job).")
@json_body_options
@click.pass_context
def application_info(ctx, id_, submitted_form_instance_id, expand, json_flag, json_file):
    """POST application.info — supply --id OR --submitted-form-instance-id."""
    if not id_ and not submitted_form_instance_id and not (json_flag or json_file):
        raise click.UsageError("Pass --id or --submitted-form-instance-id")
    run_post(ctx, "application.info", json_flag, json_file, {
        "applicationId": id_,
        "submittedFormInstanceId": submitted_form_instance_id,
        "expand": list(expand) if expand else None,
    })


@application.command("list")
@pagination_options
@click.option("--status", help="Filter by application status (Active, Hired, Archived).")
@click.option("--job-id", "job_id", help="Filter by job UUID.")
@json_body_options
@click.pass_context
def application_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                     status, job_id, json_flag, json_file):
    """POST application.list"""
    extra = load_body(json_flag, json_file, {"status": status, "jobId": job_id})
    run_list(ctx, "application.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)


@application.command("list-history")
@click.option("--id", "id_", required=True, help="Application UUID (sent as applicationId).")
@json_body_options
@click.pass_context
def application_list_history(ctx, id_, json_flag, json_file):
    """POST application.listHistory"""
    run_post(ctx, "application.listHistory", json_flag, json_file, {"applicationId": id_})
