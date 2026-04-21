from __future__ import annotations

import os

import click

from ..client import ClientError
from ..io_utils import load_body
from ..output import emit, emit_client_error
from ._base import get_client, json_body_options, pagination_options, run_list, run_post


@click.group()
def candidate():
    """Candidate endpoints (candidate.*)."""


@candidate.command("create")
@click.option("--name", required=True, help="Candidate full name.")
@click.option("--email", help="Primary personal email.")
@click.option("--phone-number", "phone_number", help="Primary phone number.")
@click.option("--linkedin-url", "linkedin_url", help="LinkedIn profile URL.")
@click.option("--github-url", "github_url", help="GitHub profile URL.")
@click.option("--website", help="Personal website URL.")
@click.option("--source-id", "source_id", help="Source UUID to attribute the candidate to.")
@click.option("--credited-to-user-id", "credited_to_user_id", help="User UUID to credit.")
@click.option("--created-at", "created_at", help="ISO 8601 timestamp; defaults to now on server.")
@json_body_options
@click.pass_context
def candidate_create(ctx, name, email, phone_number, linkedin_url, github_url, website,
                     source_id, credited_to_user_id, created_at, json_flag, json_file):
    """POST candidate.create"""
    run_post(ctx, "candidate.create", json_flag, json_file, {
        "name": name,
        "email": email,
        "phoneNumber": phone_number,
        "linkedInUrl": linkedin_url,
        "githubUrl": github_url,
        "website": website,
        "sourceId": source_id,
        "creditedToUserId": credited_to_user_id,
        "createdAt": created_at,
    })


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


@candidate.command("update")
@click.option("--id", "id_", required=True, help="Candidate UUID (sent as candidateId).")
@click.option("--name")
@click.option("--email")
@click.option("--phone-number", "phone_number")
@click.option("--linkedin-url", "linkedin_url")
@click.option("--github-url", "github_url")
@click.option("--website")
@click.option("--source-id", "source_id")
@click.option("--credited-to-user-id", "credited_to_user_id")
@json_body_options
@click.pass_context
def candidate_update(ctx, id_, name, email, phone_number, linkedin_url, github_url, website,
                     source_id, credited_to_user_id, json_flag, json_file):
    """POST candidate.update"""
    run_post(ctx, "candidate.update", json_flag, json_file, {
        "candidateId": id_,
        "name": name,
        "email": email,
        "phoneNumber": phone_number,
        "linkedInUrl": linkedin_url,
        "githubUrl": github_url,
        "website": website,
        "sourceId": source_id,
        "creditedToUserId": credited_to_user_id,
    })


@candidate.command("add-project")
@click.option("--id", "id_", required=True)
@click.option("--project-id", "project_id", required=True)
@json_body_options
@click.pass_context
def candidate_add_project(ctx, id_, project_id, json_flag, json_file):
    """POST candidate.addProject"""
    run_post(ctx, "candidate.addProject", json_flag, json_file, {
        "candidateId": id_,
        "projectId": project_id,
    })


@candidate.command("remove-project")
@click.option("--id", "id_", required=True)
@click.option("--project-id", "project_id", required=True)
@json_body_options
@click.pass_context
def candidate_remove_project(ctx, id_, project_id, json_flag, json_file):
    """POST candidate.removeProject"""
    run_post(ctx, "candidate.removeProject", json_flag, json_file, {
        "candidateId": id_,
        "projectId": project_id,
    })


def _upload(ctx, path: str, id_: str, file_path: str, field: str):
    client = get_client(ctx)
    try:
        with open(file_path, "rb") as fh:
            files = {field: (os.path.basename(file_path), fh, "application/octet-stream")}
            body = {"candidateId": id_}
            result = client.post(path, body, files=files)
    except ClientError as e:
        emit_client_error(e)
        return
    except OSError as e:
        raise click.UsageError(f"Cannot read --file {file_path!r}: {e}")
    emit(result)


@candidate.command("upload-resume")
@click.option("--id", "id_", required=True)
@click.option("--file", "file_path",
              type=click.Path(exists=True, dir_okay=False, readable=True),
              required=True, help="Path to a resume file (PDF/DOCX).")
@click.pass_context
def candidate_upload_resume(ctx, id_, file_path):
    """POST candidate.uploadResume (multipart)."""
    _upload(ctx, "candidate.uploadResume", id_, file_path, field="resume")


@candidate.command("upload-file")
@click.option("--id", "id_", required=True)
@click.option("--file", "file_path",
              type=click.Path(exists=True, dir_okay=False, readable=True),
              required=True)
@click.pass_context
def candidate_upload_file(ctx, id_, file_path):
    """POST candidate.uploadFile (multipart)."""
    _upload(ctx, "candidate.uploadFile", id_, file_path, field="file")
