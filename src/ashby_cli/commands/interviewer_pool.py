from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group("interviewer-pool")
def interviewer_pool():
    """InterviewerPool endpoints (interviewerPool.*)."""


@interviewer_pool.command("info")
@click.option("--id", "id_", required=True, help="Pool UUID (sent as interviewerPoolId).")
@json_body_options
@click.pass_context
def interviewer_pool_info(ctx, id_, json_flag, json_file):
    """POST interviewerPool.info"""
    run_post(ctx, "interviewerPool.info", json_flag, json_file, {"interviewerPoolId": id_})


@interviewer_pool.command("list")
@pagination_options
@click.option("--include-archived-pools", "include_archived_pools",
              is_flag=True, default=False,
              help="Include archived pools in the response.")
@click.option("--include-archived-training-stages", "include_archived_training_stages",
              is_flag=True, default=False,
              help="Include archived training stages in the response.")
@json_body_options
@click.pass_context
def interviewer_pool_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                          include_archived_pools, include_archived_training_stages,
                          json_flag, json_file):
    """POST interviewerPool.list"""
    flag_fields: dict = {}
    if include_archived_pools:
        flag_fields["includeArchivedPools"] = True
    if include_archived_training_stages:
        flag_fields["includeArchivedTrainingStages"] = True
    extra = load_body(json_flag, json_file, flag_fields)
    run_list(ctx, "interviewerPool.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
