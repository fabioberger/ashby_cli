from __future__ import annotations

import json
import sys
from copy import deepcopy
from typing import Any

import click


def deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in override.items():
        if v is None:
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _parse_json_text(raw: str) -> dict:
    raw = raw.strip()
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"Invalid JSON: {e}")
    if not isinstance(obj, dict):
        raise click.UsageError("JSON body must be an object at the top level")
    return obj


def load_body(
    json_flag: str | None,
    json_file: str | None,
    flag_fields: dict[str, Any],
) -> dict:
    if json_flag is not None and json_file is not None:
        raise click.UsageError("Provide at most one of --json or --json-file")

    raw: str | None = None
    if json_flag is not None:
        raw = sys.stdin.read() if json_flag == "-" else json_flag
    elif json_file is not None:
        if json_file == "-":
            raw = sys.stdin.read()
        else:
            try:
                with open(json_file, "r", encoding="utf-8") as fh:
                    raw = fh.read()
            except OSError as e:
                raise click.UsageError(f"Cannot read --json-file {json_file!r}: {e}")

    body = _parse_json_text(raw) if raw is not None else {}
    cleaned = {k: v for k, v in flag_fields.items() if v is not None}
    return deep_merge(body, cleaned)
