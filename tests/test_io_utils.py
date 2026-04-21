import io
import json

import click
import pytest

from ashby_cli.io_utils import deep_merge, load_body


def test_deep_merge_drops_none_and_overrides_scalars():
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": None}
    override = {"a": 10, "b": {"c": 20}, "e": None, "f": None}
    assert deep_merge(base, override) == {"a": 10, "b": {"c": 20, "d": 3}, "e": None}


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    _ = deep_merge(base, {"a": {"b": 2}})
    assert base == {"a": {"b": 1}}


def test_load_body_merges_flags_over_json():
    body = load_body(json_flag='{"name": "Alice", "email": "a@x"}',
                     json_file=None,
                     flag_fields={"email": "override@x", "phone": None})
    assert body == {"name": "Alice", "email": "override@x"}


def test_load_body_rejects_both_sources():
    with pytest.raises(click.UsageError):
        load_body(json_flag='{}', json_file='x.json', flag_fields={})


def test_load_body_rejects_non_object_json():
    with pytest.raises(click.UsageError):
        load_body(json_flag='[1, 2, 3]', json_file=None, flag_fields={})


def test_load_body_rejects_invalid_json():
    with pytest.raises(click.UsageError):
        load_body(json_flag='{not json}', json_file=None, flag_fields={})


def test_load_body_empty_returns_flags_only():
    body = load_body(None, None, {"a": 1, "b": None})
    assert body == {"a": 1}


def test_load_body_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"stdin": true}'))
    body = load_body(json_flag="-", json_file=None, flag_fields={"extra": "yes"})
    assert body == {"stdin": True, "extra": "yes"}


def test_load_body_file(tmp_path):
    p = tmp_path / "body.json"
    p.write_text(json.dumps({"fromFile": True}))
    body = load_body(None, str(p), {})
    assert body == {"fromFile": True}
