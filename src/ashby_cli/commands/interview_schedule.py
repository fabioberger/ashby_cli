from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group("interview-schedule")
def interview_schedule():
    """InterviewSchedule endpoints (interviewSchedule.*)."""


@interview_schedule.command("create")
@click.option("--application-id", "application_id", required=True)
@click.option("--interview-stage-id", "interview_stage_id",
              help="Stage to schedule under (optional; defaults to current).")
@json_body_options
@click.pass_context
def interview_schedule_create(ctx, application_id, interview_stage_id, json_flag, json_file):
    """POST interviewSchedule.create — use --json-file to pass the interviewEvents array."""
    run_post(ctx, "interviewSchedule.create", json_flag, json_file, {
        "applicationId": application_id,
        "interviewStageId": interview_stage_id,
    })


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


@interview_schedule.command("update")
@click.option("--id", "id_", required=True, help="Schedule UUID (sent as interviewScheduleId).")
@json_body_options
@click.pass_context
def interview_schedule_update(ctx, id_, json_flag, json_file):
    """POST interviewSchedule.update — pass mutation payload via --json or --json-file."""
    run_post(ctx, "interviewSchedule.update", json_flag, json_file, {
        "interviewScheduleId": id_,
    })


@interview_schedule.command("cancel")
@click.option("--id", "id_", required=True, help="Schedule UUID (sent as interviewScheduleId).")
@json_body_options
@click.pass_context
def interview_schedule_cancel(ctx, id_, json_flag, json_file):
    """POST interviewSchedule.cancel"""
    run_post(ctx, "interviewSchedule.cancel", json_flag, json_file, {"interviewScheduleId": id_})
