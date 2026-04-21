from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def interview():
    """Interview endpoints (interview.*)."""


@interview.command("info")
@click.option("--id", "id_", required=True, help="Interview UUID (sent as id).")
@json_body_options
@click.pass_context
def interview_info(ctx, id_, json_flag, json_file):
    """POST interview.info"""
    run_post(ctx, "interview.info", json_flag, json_file, {"id": id_})


@interview.command("list")
@pagination_options
@json_body_options
@click.pass_context
def interview_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                   json_flag, json_file):
    """POST interview.list"""
    extra = load_body(json_flag, json_file, {})
    run_list(ctx, "interview.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
