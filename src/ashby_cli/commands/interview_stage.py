from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group("interview-stage")
def interview_stage():
    """InterviewStage endpoints (interviewStage.*)."""


@interview_stage.command("info")
@click.option("--id", "id_", required=True, help="Stage UUID (sent as interviewStageId).")
@json_body_options
@click.pass_context
def interview_stage_info(ctx, id_, json_flag, json_file):
    """POST interviewStage.info"""
    run_post(ctx, "interviewStage.info", json_flag, json_file, {"interviewStageId": id_})


@interview_stage.command("list")
@pagination_options
@click.option("--interview-plan-id", "interview_plan_id", required=True,
              help="Plan UUID whose stages to list.")
@json_body_options
@click.pass_context
def interview_stage_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                         interview_plan_id, json_flag, json_file):
    """POST interviewStage.list"""
    extra = load_body(json_flag, json_file, {"interviewPlanId": interview_plan_id})
    run_list(ctx, "interviewStage.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
