from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def application():
    """Application endpoints (application.*)."""


@application.command("create")
@click.option("--candidate-id", "candidate_id", required=True)
@click.option("--job-id", "job_id", required=True)
@click.option("--interview-plan-id", "interview_plan_id")
@click.option("--source-id", "source_id")
@click.option("--credited-to-user-id", "credited_to_user_id")
@click.option("--created-at", "created_at")
@json_body_options
@click.pass_context
def application_create(ctx, candidate_id, job_id, interview_plan_id, source_id,
                       credited_to_user_id, created_at, json_flag, json_file):
    """POST application.create"""
    run_post(ctx, "application.create", json_flag, json_file, {
        "candidateId": candidate_id,
        "jobId": job_id,
        "interviewPlanId": interview_plan_id,
        "sourceId": source_id,
        "creditedToUserId": credited_to_user_id,
        "createdAt": created_at,
    })


@application.command("info")
@click.option("--id", "id_", help="Application UUID (sent as applicationId).")
@click.option("--submitted-form-instance-id", "submitted_form_instance_id")
@click.option("--expand", multiple=True,
              help="Repeatable. Expand related objects (e.g. candidate, job).")
@json_body_options
@click.pass_context
def application_info(ctx, id_, submitted_form_instance_id, expand, json_flag, json_file):
    """POST application.info — supply --id OR --submitted-form-instance-id."""
    if not id_ and not submitted_form_instance_id and not (json_flag or json_file):
        raise click.UsageError("Pass --id or --submitted-form-instance-id")
    run_post(ctx, "application.info", json_flag, json_file, {
        "applicationId": id_,
        "submittedFormInstanceId": submitted_form_instance_id,
        "expand": list(expand) if expand else None,
    })


@application.command("list")
@pagination_options
@click.option("--status", help="Filter by application status (Active, Hired, Archived).")
@click.option("--job-id", "job_id", help="Filter by job UUID.")
@json_body_options
@click.pass_context
def application_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages,
                     status, job_id, json_flag, json_file):
    """POST application.list"""
    extra = load_body(json_flag, json_file, {"status": status, "jobId": job_id})
    run_list(ctx, "application.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)


@application.command("update")
@click.option("--id", "id_", required=True, help="Application UUID (sent as applicationId).")
@click.option("--source-id", "source_id")
@click.option("--credited-to-user-id", "credited_to_user_id")
@json_body_options
@click.pass_context
def application_update(ctx, id_, source_id, credited_to_user_id, json_flag, json_file):
    """POST application.update"""
    run_post(ctx, "application.update", json_flag, json_file, {
        "applicationId": id_,
        "sourceId": source_id,
        "creditedToUserId": credited_to_user_id,
    })


@application.command("change-stage")
@click.option("--id", "id_", required=True)
@click.option("--interview-stage-id", "interview_stage_id", required=True)
@json_body_options
@click.pass_context
def application_change_stage(ctx, id_, interview_stage_id, json_flag, json_file):
    """POST application.changeStage"""
    run_post(ctx, "application.changeStage", json_flag, json_file, {
        "applicationId": id_,
        "interviewStageId": interview_stage_id,
    })


@application.command("change-source")
@click.option("--id", "id_", required=True)
@click.option("--source-id", "source_id", required=True)
@json_body_options
@click.pass_context
def application_change_source(ctx, id_, source_id, json_flag, json_file):
    """POST application.changeSource"""
    run_post(ctx, "application.changeSource", json_flag, json_file, {
        "applicationId": id_,
        "sourceId": source_id,
    })


@application.command("transfer")
@click.option("--id", "id_", required=True, help="Application UUID to transfer.")
@click.option("--target-job-id", "target_job_id", required=True)
@json_body_options
@click.pass_context
def application_transfer(ctx, id_, target_job_id, json_flag, json_file):
    """POST application.transfer"""
    run_post(ctx, "application.transfer", json_flag, json_file, {
        "applicationId": id_,
        "targetJobId": target_job_id,
    })


@application.command("hire")
@click.option("--id", "id_", required=True)
@click.option("--start-date", "start_date", help="ISO date (YYYY-MM-DD).")
@json_body_options
@click.pass_context
def application_hire(ctx, id_, start_date, json_flag, json_file):
    """POST application.hire"""
    run_post(ctx, "application.hire", json_flag, json_file, {
        "applicationId": id_,
        "startDate": start_date,
    })


@application.command("unreject")
@click.option("--id", "id_", required=True)
@json_body_options
@click.pass_context
def application_unreject(ctx, id_, json_flag, json_file):
    """POST application.unreject"""
    run_post(ctx, "application.unreject", json_flag, json_file, {"applicationId": id_})


@application.command("reject")
@click.option("--id", "id_", required=True)
@click.option("--archive-reason-id", "archive_reason_id")
@click.option("--reject-in-source/--no-reject-in-source", "reject_in_source", default=None)
@json_body_options
@click.pass_context
def application_reject(ctx, id_, archive_reason_id, reject_in_source, json_flag, json_file):
    """POST application.reject"""
    run_post(ctx, "application.reject", json_flag, json_file, {
        "applicationId": id_,
        "archiveReasonId": archive_reason_id,
        "rejectInSource": reject_in_source,
    })


@application.command("list-history")
@click.option("--id", "id_", required=True, help="Application UUID (sent as applicationId).")
@json_body_options
@click.pass_context
def application_list_history(ctx, id_, json_flag, json_file):
    """POST application.listHistory"""
    run_post(ctx, "application.listHistory", json_flag, json_file, {"applicationId": id_})
