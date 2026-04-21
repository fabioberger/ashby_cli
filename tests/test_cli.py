import base64
import json

import pytest
import responses
from click.testing import CliRunner

from ashby_cli.cli import main
from ashby_cli.client import BASE_URL


ALL_RESOURCE_GROUPS = [
    "candidate", "file", "job", "job-posting", "application",
    "interview-event", "interview-plan", "interview-schedule",
    "interview-stage", "interview-stage-group", "interview",
    "interviewer-pool",
]


@pytest.fixture
def runner():
    return CliRunner()


def test_root_help_lists_all_groups(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0, result.output
    for group in ALL_RESOURCE_GROUPS:
        assert group in result.output, f"missing {group}"


@pytest.mark.parametrize("group", ALL_RESOURCE_GROUPS)
def test_each_group_help(runner, group):
    result = runner.invoke(main, [group, "--help"])
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


@responses.activate
def test_candidate_info_emits_compact_json(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.info",
        json={"success": True, "results": {"id": "u1", "name": "Alice"}},
        status=200,
    )
    result = runner.invoke(main, ["candidate", "info", "--id", "u1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload == {"ok": True, "data": {"id": "u1", "name": "Alice"}}


@responses.activate
def test_candidate_info_error_exit_code_1(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.info",
        json={"success": False, "errorInfo": {"code": "not_found", "message": "x"}},
        status=200,
    )
    result = runner.invoke(main, ["candidate", "info", "--id", "nope"])
    assert result.exit_code == 1
    payload = json.loads(result.output.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_found"


@responses.activate
def test_candidate_list_single_page_surfaces_cursor(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 1}], "moreDataAvailable": True, "nextCursor": "next"},
        status=200,
    )
    result = runner.invoke(main, ["candidate", "list", "--limit", "1"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload["ok"] is True
    assert payload["moreDataAvailable"] is True
    assert payload["nextCursor"] == "next"


@responses.activate
def test_candidate_list_all_merges_pages(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 1}], "moreDataAvailable": True, "nextCursor": "p2"},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 2}], "moreDataAvailable": False, "syncToken": "s1"},
        status=200,
    )
    result = runner.invoke(main, ["candidate", "list", "--all"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload["data"] == [{"id": 1}, {"id": 2}]
    assert payload["moreDataAvailable"] is False
    assert payload["syncToken"] == "s1"
    assert payload["pagesWalked"] == 2


@responses.activate
def test_candidate_search_flags_become_body(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.search",
        json={"success": True, "results": []},
        status=200,
    )
    result = runner.invoke(main, [
        "candidate", "search",
        "--email", "a@x",
        "--name", "Alice",
    ])
    assert result.exit_code == 0, result.output
    sent = json.loads(responses.calls[0].request.body)
    assert sent == {"email": "a@x", "name": "Alice"}
    auth = responses.calls[0].request.headers["Authorization"]
    assert auth == "Basic " + base64.b64encode(b"test-key:").decode()


@responses.activate
def test_json_body_with_flag_override(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.search",
        json={"success": True, "results": []},
        status=200,
    )
    result = runner.invoke(main, [
        "candidate", "search",
        "--name", "FromFlag",
        "--json", '{"name": "FromJson", "email": "extra@x"}',
    ])
    assert result.exit_code == 0, result.output
    sent = json.loads(responses.calls[0].request.body)
    assert sent["name"] == "FromFlag"
    assert sent["email"] == "extra@x"


@responses.activate
def test_pretty_output_is_indented(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.info",
        json={"success": True, "results": {"id": "u1"}},
        status=200,
    )
    result = runner.invoke(main, ["--pretty", "candidate", "info", "--id", "u1"])
    assert result.exit_code == 0
    # pretty output has indentation
    assert "\n  " in result.output


def test_missing_api_key_exits_2(runner, monkeypatch):
    monkeypatch.delenv("ASHBY_API_KEY", raising=False)
    result = runner.invoke(main, ["candidate", "info", "--id", "x"])
    payload = json.loads(result.output.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_api_key"
    assert result.exit_code == 2


@responses.activate
def test_rate_limited_emits_envelope_exit_4(runner):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={},
        status=429,
        headers={"Retry-After": "30"},
    )
    result = runner.invoke(main, ["candidate", "list"])
    assert result.exit_code == 4
    payload = json.loads(result.output.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "rate_limited"
    assert payload["error"]["retryAfter"] == "30"


@responses.activate
def test_invalid_json_body_exits_usage(runner):
    result = runner.invoke(main, ["candidate", "info", "--id", "x", "--json", "{bad}"])
    # usage error: click emits to stderr with exit code 2
    assert result.exit_code == 2


@responses.activate
def test_interview_stage_list_requires_plan_id(runner):
    result = runner.invoke(main, ["interview-stage", "list"])
    assert result.exit_code == 2
    assert "interview-plan-id" in result.output.lower() or "Missing option" in result.output


@responses.activate
def test_application_info_requires_one_id(runner):
    result = runner.invoke(main, ["application", "info"])
    assert result.exit_code == 2


@responses.activate
@pytest.mark.parametrize("cmd, path", [
    (["file", "info", "--file-handle", "h"], "file.info"),
    (["job", "info", "--id", "j"], "job.info"),
    (["job-posting", "info", "--id", "p"], "jobPosting.info"),
    (["interview", "info", "--id", "i"], "interview.info"),
    (["interview-stage", "info", "--id", "s"], "interviewStage.info"),
    (["interviewer-pool", "info", "--id", "p"], "interviewerPool.info"),
])
def test_endpoint_paths_match_inventory(runner, cmd, path):
    responses.add(responses.POST, f"{BASE_URL}/{path}", json={"success": True, "results": {}}, status=200)
    result = runner.invoke(main, cmd)
    assert result.exit_code == 0, result.output
    assert responses.calls[0].request.url.endswith(path)


@responses.activate
def test_module_entrypoint_runs():
    """`python -m ashby_cli --help` should work."""
    import subprocess, sys
    r = subprocess.run([sys.executable, "-m", "ashby_cli", "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "Agent-friendly" in r.stdout or "Usage:" in r.stdout


def test_subprocess_usage_error_emits_json_envelope():
    """main_entry wraps Click's UsageError into a JSON envelope so agents always parse stdout."""
    import subprocess, sys, json as _json
    r = subprocess.run(
        [sys.executable, "-m", "ashby_cli", "candidate", "info"],
        capture_output=True, text=True,
        env={"ASHBY_API_KEY": "test-key", "PATH": __import__("os").environ["PATH"]},
    )
    assert r.returncode == 2, r.stderr
    payload = _json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "usage"
    assert "--id" in payload["error"]["message"]


def test_subprocess_missing_api_key_emits_envelope():
    import subprocess, sys, json as _json, os
    env = {k: v for k, v in os.environ.items() if k != "ASHBY_API_KEY"}
    r = subprocess.run(
        [sys.executable, "-m", "ashby_cli", "candidate", "info", "--id", "x"],
        capture_output=True, text=True, env=env,
    )
    assert r.returncode == 2
    payload = _json.loads(r.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_api_key"
