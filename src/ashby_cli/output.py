from __future__ import annotations

import json
import sys
from typing import Any

from .client import EnvelopeResult, ClientError, EXIT_API_ERROR

_pretty: bool = False


def set_pretty(value: bool) -> None:
    global _pretty
    _pretty = bool(value)


def dumps(payload: Any) -> str:
    if _pretty:
        return json.dumps(payload, indent=2, sort_keys=True, default=str)
    return json.dumps(payload, separators=(",", ":"), default=str, sort_keys=False)


def _emit(payload: dict, exit_code: int) -> None:
    sys.stdout.write(dumps(payload) + "\n")
    sys.stdout.flush()
    if exit_code != 0:
        sys.exit(exit_code)


def emit(result: EnvelopeResult) -> None:
    if result.ok:
        payload: dict[str, Any] = {"ok": True, "data": result.data}
        if result.more is not None:
            payload["moreDataAvailable"] = result.more
        if result.next_cursor is not None:
            payload["nextCursor"] = result.next_cursor
        if result.sync_token is not None:
            payload["syncToken"] = result.sync_token
        if result.request_id is not None:
            payload["requestId"] = result.request_id
        _emit(payload, 0)
    else:
        payload = {"ok": False, "error": dict(result.error or {})}
        exit_code = result.exit_code or EXIT_API_ERROR
        _emit(payload, exit_code)


def emit_many(results: list[EnvelopeResult]) -> None:
    merged: list = []
    last: EnvelopeResult | None = None
    pages_walked = 0
    for r in results:
        if not r.ok:
            emit(r)
            return
        if isinstance(r.data, list):
            merged.extend(r.data)
        elif r.data is None:
            pass
        else:
            merged.append(r.data)
        last = r
        pages_walked += 1
    if last is None:
        _emit({"ok": True, "data": [], "moreDataAvailable": False, "pagesWalked": 0}, 0)
        return
    payload: dict[str, Any] = {
        "ok": True,
        "data": merged,
        "pagesWalked": pages_walked,
        "moreDataAvailable": bool(last.more),
    }
    if last.next_cursor is not None:
        payload["nextCursor"] = last.next_cursor
    if last.sync_token is not None:
        payload["syncToken"] = last.sync_token
    if last.request_id is not None:
        payload["requestId"] = last.request_id
    _emit(payload, 0)


def emit_client_error(err: ClientError) -> None:
    emit(err.to_envelope())
