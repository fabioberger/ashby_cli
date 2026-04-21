from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def job():
    """Job endpoints (job.*) — read-only."""


@job.command("info")
@click.option("--id", "id_", required=True, help="Job UUID (sent as id).")
@json_body_options
@click.pass_context
def job_info(ctx, id_, json_flag, json_file):
    """POST job.info"""
    run_post(ctx, "job.info", json_flag, json_file, {"id": id_})


@job.command("list")
@pagination_options
@click.option("--status", help="Filter by job status (e.g. Open, Closed, Archived, Draft).")
@json_body_options
@click.pass_context
def job_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages, status,
             json_flag, json_file):
    """POST job.list"""
    extra = load_body(json_flag, json_file, {"status": status})
    run_list(ctx, "job.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)


@job.command("search")
@click.option("--title")
@click.option("--identifier")
@json_body_options
@click.pass_context
def job_search(ctx, title, identifier, json_flag, json_file):
    """POST job.search (best-effort name/id match; non-paginated)."""
    run_post(ctx, "job.search", json_flag, json_file, {
        "title": title,
        "identifier": identifier,
    })
