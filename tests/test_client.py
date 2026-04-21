import base64
import json

import pytest
import responses

from ashby_cli.client import AshbyClient, ClientError, BASE_URL


@pytest.fixture
def client():
    return AshbyClient(api_key="test-key", base_url=BASE_URL, timeout=5.0)


def _expected_auth_header() -> str:
    # Basic auth: base64(api_key:)
    return "Basic " + base64.b64encode(b"test-key:").decode()


@responses.activate
def test_post_success_envelope_parsed(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.info",
        json={"success": True, "results": {"id": "abc", "name": "Alice"}},
        status=200,
    )
    result = client.post("candidate.info", {"id": "abc"})
    assert result.ok is True
    assert result.data == {"id": "abc", "name": "Alice"}
    assert result.error is None

    call = responses.calls[0]
    assert call.request.headers["Authorization"] == _expected_auth_header()
    assert call.request.headers["Content-Type"] == "application/json"
    assert call.request.headers["Accept"] == "application/json"
    assert json.loads(call.request.body) == {"id": "abc"}


@responses.activate
def test_post_pagination_fields_surfaced(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={
            "success": True,
            "results": [{"id": "1"}, {"id": "2"}],
            "moreDataAvailable": True,
            "nextCursor": "cur-xyz",
            "syncToken": None,
        },
        status=200,
    )
    result = client.post("candidate.list", {"limit": 2})
    assert result.ok is True
    assert result.more is True
    assert result.next_cursor == "cur-xyz"
    assert len(result.data) == 2


@responses.activate
def test_post_error_envelope_with_errorInfo(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.info",
        json={"success": False, "errorInfo": {"code": "not_found", "message": "nope"}},
        status=200,
    )
    result = client.post("candidate.info", {"id": "bad"})
    assert result.ok is False
    assert result.error["code"] == "not_found"
    assert result.error["message"] == "nope"
    assert result.error["httpStatus"] == 200


@responses.activate
def test_post_error_envelope_with_errors_array(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": False, "errors": ["sync_token_expired"]},
        status=200,
    )
    result = client.post("candidate.list", {"syncToken": "old"})
    assert result.ok is False
    assert result.error["code"] == "api_error"
    assert "sync_token_expired" in result.error["message"]


@responses.activate
def test_rate_limited_raises_client_error(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": False},
        status=429,
        headers={"Retry-After": "30"},
    )
    with pytest.raises(ClientError) as ei:
        client.post("candidate.list", {})
    assert ei.value.code == "rate_limited"
    assert ei.value.exit_code == 4


@responses.activate
def test_server_error_raises(client):
    responses.add(responses.POST, f"{BASE_URL}/candidate.list", body="oops", status=503)
    with pytest.raises(ClientError) as ei:
        client.post("candidate.list", {})
    assert ei.value.code == "server_error"
    assert ei.value.exit_code == 3


@responses.activate
def test_paginate_walks_until_no_more(client):
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 1}], "moreDataAvailable": True, "nextCursor": "p2"},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 2}], "moreDataAvailable": True, "nextCursor": "p3"},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/candidate.list",
        json={"success": True, "results": [{"id": 3}], "moreDataAvailable": False, "syncToken": "sync-1"},
        status=200,
    )

    pages = list(client.paginate("candidate.list", {"limit": 1}, max_pages=5))
    assert len(pages) == 3
    assert pages[-1].sync_token == "sync-1"
    assert pages[-1].more is False
    # second and third calls include cursor
    assert json.loads(responses.calls[1].request.body)["cursor"] == "p2"
    assert json.loads(responses.calls[2].request.body)["cursor"] == "p3"


@responses.activate
def test_paginate_respects_max_pages(client):
    for i in range(5):
        responses.add(
            responses.POST,
            f"{BASE_URL}/candidate.list",
            json={"success": True, "results": [{"id": i}], "moreDataAvailable": True, "nextCursor": f"p{i+1}"},
            status=200,
        )
    pages = list(client.paginate("candidate.list", {}, max_pages=2))
    assert len(pages) == 2


def test_missing_api_key_raises_usage(monkeypatch):
    monkeypatch.delenv("ASHBY_API_KEY", raising=False)
    with pytest.raises(ClientError) as ei:
        AshbyClient()
    assert ei.value.exit_code == 2
    assert "ASHBY_API_KEY" in ei.value.message
