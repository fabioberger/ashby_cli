from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def candidate():
    """Candidate endpoints (candidate.*) — read-only."""


@candidate.command("info")
@click.option("--id", "id_", required=True, help="Candidate UUID.")
@json_body_options
@click.pass_context
def candidate_info(ctx, id_, json_flag, json_file):
    """POST candidate.info"""
    run_post(ctx, "candidate.info", json_flag, json_file, {"id": id_})


@candidate.command("list")
@pagination_options
@json_body_options
@click.pass_context
def candidate_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                   json_flag, json_file):
    """POST candidate.list"""
    extra = load_body(json_flag, json_file, {})
    run_list(ctx, "candidate.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)


@candidate.command("search")
@click.option("--email", help="Exact email match.")
@click.option("--name", help="Fuzzy name match.")
@json_body_options
@click.pass_context
def candidate_search(ctx, email, name, json_flag, json_file):
    """POST candidate.search (returns up to 100 matches, no pagination)."""
    run_post(ctx, "candidate.search", json_flag, json_file, {
        "email": email,
        "name": name,
    })
