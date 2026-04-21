from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list


@click.group("interview-plan")
def interview_plan():
    """InterviewPlan endpoints (interviewPlan.*)."""


@interview_plan.command("list")
@pagination_options
@json_body_options
@click.pass_context
def interview_plan_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                        json_flag, json_file):
    """POST interviewPlan.list"""
    extra = load_body(json_flag, json_file, {})
    run_list(ctx, "interviewPlan.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
