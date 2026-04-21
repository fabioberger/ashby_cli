from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list


@click.group("interview-event")
def interview_event():
    """InterviewEvent endpoints (interviewEvent.*)."""


@interview_event.command("list")
@pagination_options
@click.option("--interview-schedule-id", "interview_schedule_id", required=True,
              help="Filter events for a specific schedule (required by Ashby).")
@json_body_options
@click.pass_context
def interview_event_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                         interview_schedule_id, json_flag, json_file):
    """POST interviewEvent.list"""
    extra = load_body(json_flag, json_file, {
        "interviewScheduleId": interview_schedule_id,
    })
    run_list(ctx, "interviewEvent.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)
