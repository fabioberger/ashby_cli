from __future__ import annotations

from typing import Any

import click

from ..client import AshbyClient, ClientError
from ..io_utils import load_body
from ..output import emit, emit_client_error, emit_many


def json_body_options(f):
    f = click.option(
        "--json-file",
        "json_file",
        default=None,
        metavar="PATH",
        help="Read JSON body from file ('-' reads stdin).",
    )(f)
    f = click.option(
        "--json",
        "json_flag",
        default=None,
        metavar="JSON",
        help="Inline JSON body ('-' reads stdin). Flags override keys in this JSON.",
    )(f)
    return f


def pagination_options(f):
    f = click.option("--max-pages", type=int, default=50, show_default=True,
                     help="Maximum pages walked when --all is set.")(f)
    f = click.option("--all", "walk_all", is_flag=True, default=False,
                     help="Walk pages until the API reports no more data (safety-capped by --max-pages).")(f)
    f = click.option("--created-after", "created_after", type=int, default=None,
                     help="Filter: Unix epoch in milliseconds.")(f)
    f = click.option("--sync-token", "sync_token", default=None,
                     help="Opaque sync token for incremental sync.")(f)
    f = click.option("--limit", type=int, default=None,
                     help="Max items per page (Ashby default/max: 100).")(f)
    f = click.option("--cursor", default=None,
                     help="Opaque pagination cursor from a prior response.")(f)
    return f


def get_client(ctx) -> AshbyClient:
    """Lazy singleton: only constructs AshbyClient (and validates API key) when actually needed."""
    root = ctx.find_root().obj
    client = root.get("_client")
    if client is None:
        client = AshbyClient(
            api_key=root.get("api_key"),
            base_url=root.get("base_url", "https://api.ashbyhq.com"),
            timeout=root.get("timeout", 30.0),
        )
        root["_client"] = client
    return client


def safe_call(func):
    """Catches ClientError and turns it into a JSON envelope so agents always get parseable output."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            emit_client_error(e)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def run_post(
    ctx,
    path: str,
    json_flag: str | None,
    json_file: str | None,
    flag_fields: dict[str, Any] | None = None,
    *,
    files: dict | None = None,
) -> None:
    body = load_body(json_flag, json_file, flag_fields or {})
    try:
        result = get_client(ctx).post(path, body, files=files)
    except ClientError as e:
        emit_client_error(e)
        return
    emit(result)


def run_list(
    ctx,
    path: str,
    *,
    cursor: str | None,
    limit: int | None,
    sync_token: str | None,
    created_after: int | None,
    walk_all: bool,
    max_pages: int,
    extra_body: dict | None = None,
) -> None:
    body: dict = dict(extra_body or {})
    if cursor is not None:
        body["cursor"] = cursor
    if limit is not None:
        body["limit"] = limit
    if sync_token is not None:
        body["syncToken"] = sync_token
    if created_after is not None:
        body["createdAfter"] = created_after

    client = get_client(ctx)
    try:
        if walk_all:
            results = list(client.paginate(path, body, max_pages=max_pages))
            emit_many(results)
        else:
            emit(client.post(path, body))
    except ClientError as e:
        emit_client_error(e)
