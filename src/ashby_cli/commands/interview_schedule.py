from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list


@click.group("interview-schedule")
def interview_schedule():
    """InterviewSchedule endpoints (interviewSchedule.*) — read-only."""


@interview_schedule.command("list")
@pagination_options
@click.option("--application-id", "application_id")
@json_body_options
@click.pass_context
def interview_schedule_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                            application_id, json_flag, json_file):
    """POST interviewSchedule.list"""
    extra = load_body(json_flag, json_file, {"applicationId": application_id})
    run_list(ctx, "interviewSchedule.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
