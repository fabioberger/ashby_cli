from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group("job-posting")
def job_posting():
    """JobPosting endpoints (jobPosting.*) — read-only."""


@job_posting.command("info")
@click.option("--id", "id_", required=True, help="JobPosting UUID (sent as jobPostingId).")
@json_body_options
@click.pass_context
def job_posting_info(ctx, id_, json_flag, json_file):
    """POST jobPosting.info"""
    run_post(ctx, "jobPosting.info", json_flag, json_file, {"jobPostingId": id_})


@job_posting.command("list")
@pagination_options
@click.option("--location-id", "location_id")
@click.option("--list-all-statuses", "list_all_statuses", is_flag=True, default=False,
              help="Include non-Published postings (requires elevated scope).")
@json_body_options
@click.pass_context
def job_posting_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                     location_id, list_all_statuses, json_flag, json_file):
    """POST jobPosting.list"""
    extra = load_body(json_flag, json_file, {
        "locationId": location_id,
        "listedJobPostingsOnly": None if list_all_statuses else True,
    })
    if list_all_statuses:
        extra["listedJobPostingsOnly"] = False
    run_list(ctx, "jobPosting.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
