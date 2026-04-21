from __future__ import annotations

import click

from ..io_utils import load_body
from ._base import json_body_options, pagination_options, run_list, run_post


@click.group()
def job():
    """Job endpoints (job.*)."""


@job.command("create")
@click.option("--title", required=True)
@click.option("--team-id", "team_id", required=True)
@click.option("--location-id", "location_id", required=True)
@click.option("--department-id", "department_id")
@click.option("--employment-type", "employment_type",
              type=click.Choice(["FullTime", "PartTime", "Intern", "Contract", "Temporary"], case_sensitive=False))
@click.option("--default-interview-plan-id", "default_interview_plan_id")
@json_body_options
@click.pass_context
def job_create(ctx, title, team_id, location_id, department_id, employment_type,
               default_interview_plan_id, json_flag, json_file):
    """POST job.create"""
    run_post(ctx, "job.create", json_flag, json_file, {
        "title": title,
        "teamId": team_id,
        "locationId": location_id,
        "departmentId": department_id,
        "employmentType": employment_type,
        "defaultInterviewPlanId": default_interview_plan_id,
    })


@job.command("info")
@click.option("--id", "id_", required=True, help="Job UUID (sent as id).")
@json_body_options
@click.pass_context
def job_info(ctx, id_, json_flag, json_file):
    """POST job.info"""
    run_post(ctx, "job.info", json_flag, json_file, {"id": id_})


@job.command("list")
@pagination_options
@click.option("--status", help="Filter by job status (e.g. Open, Closed, Archived, Draft).")
@json_body_options
@click.pass_context
def job_list(ctx, cursor, limit, sync_token, created_after, walk_all, max_pages, status,
             json_flag, json_file):
    """POST job.list"""
    extra = load_body(json_flag, json_file, {"status": status})
    run_list(ctx, "job.list",
             cursor=cursor, limit=limit, sync_token=sync_token,
             created_after=created_after, walk_all=walk_all, max_pages=max_pages,
             extra_body=extra)


@job.command("update")
@click.option("--id", "id_", required=True, help="Job UUID (sent as jobId).")
@click.option("--title")
@click.option("--team-id", "team_id")
@click.option("--location-id", "location_id")
@click.option("--department-id", "department_id")
@click.option("--status", help="New status: Open, Closed, Archived, Draft.")
@click.option("--default-interview-plan-id", "default_interview_plan_id")
@json_body_options
@click.pass_context
def job_update(ctx, id_, title, team_id, location_id, department_id, status,
               default_interview_plan_id, json_flag, json_file):
    """POST job.update"""
    run_post(ctx, "job.update", json_flag, json_file, {
        "jobId": id_,
        "title": title,
        "teamId": team_id,
        "locationId": location_id,
        "departmentId": department_id,
        "status": status,
        "defaultInterviewPlanId": default_interview_plan_id,
    })


@job.command("set-status")
@click.option("--id", "id_", required=True)
@click.option("--status", required=True, help="Open, Closed, Archived, or Draft.")
@json_body_options
@click.pass_context
def job_set_status(ctx, id_, status, json_flag, json_file):
    """POST job.setStatus"""
    run_post(ctx, "job.setStatus", json_flag, json_file, {
        "jobId": id_,
        "status": status,
    })


@job.command("search")
@click.option("--title")
@click.option("--identifier")
@json_body_options
@click.pass_context
def job_search(ctx, title, identifier, json_flag, json_file):
    """POST job.search (best-effort name/id match; non-paginated)."""
    run_post(ctx, "job.search", json_flag, json_file, {
        "title": title,
        "identifier": identifier,
    })
