from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list


@click.group("interview-stage-group")
def interview_stage_group():
    """InterviewStageGroup endpoints (interviewStageGroup.*)."""


@interview_stage_group.command("list")
@pagination_options
@click.option("--interview-plan-id", "interview_plan_id", required=True,
              help="Plan UUID whose stage groups to list.")
@json_body_options
@click.pass_context
def interview_stage_group_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                               interview_plan_id, json_flag, json_file):
    """POST interviewStageGroup.list"""
    extra = load_body(json_flag, json_file, {"interviewPlanId": interview_plan_id})
    run_list(ctx, "interviewStageGroup.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
