from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterator

import requests
from requests.auth import HTTPBasicAuth

from . import __version__

BASE_URL = "https://api.ashbyhq.com"
USER_AGENT = f"ashby-cli/{__version__}"

EXIT_OK = 0
EXIT_API_ERROR = 1
EXIT_USAGE = 2
EXIT_NETWORK = 3
EXIT_RATE_LIMITED = 4


@dataclass
class EnvelopeResult:
    ok: bool
    data: Any = None
    more: bool | None = None
    next_cursor: str | None = None
    sync_token: str | None = None
    error: dict | None = None
    http_status: int = 0
    request_id: str | None = None
    exit_code: int = EXIT_OK


class ClientError(Exception):
    """Wraps a non-API failure (network, rate limit, config) in the same envelope shape."""

    def __init__(self, code: str, message: str, *, exit_code: int, http_status: int = 0, **extra: Any):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.exit_code = exit_code
        self.extra = extra

    def to_envelope(self) -> EnvelopeResult:
        err = {"code": self.code, "message": self.message, "httpStatus": self.http_status}
        err.update({k: v for k, v in self.extra.items() if v is not None})
        return EnvelopeResult(
            ok=False,
            error=err,
            http_status=self.http_status,
            exit_code=self.exit_code,
        )


class AshbyClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ):
        key = api_key if api_key is not None else os.environ.get("ASHBY_API_KEY")
        if not key:
            raise ClientError(
                "missing_api_key",
                "ASHBY_API_KEY is not set. Pass --api-key or export ASHBY_API_KEY.",
                exit_code=EXIT_USAGE,
            )
        self.api_key = key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    def _auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.api_key, "")

    def post(
        self,
        path: str,
        body: dict | None = None,
        *,
        files: dict | None = None,
    ) -> EnvelopeResult:
        url = f"{self.base_url}/{path}"
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        try:
            if files:
                form = {}
                for k, v in (body or {}).items():
                    if v is None:
                        continue
                    form[k] = v if isinstance(v, (str, bytes)) else str(v)
                resp = self._session.post(
                    url,
                    auth=self._auth(),
                    headers=headers,
                    data=form,
                    files=files,
                    timeout=self.timeout,
                )
            else:
                headers["Content-Type"] = "application/json"
                resp = self._session.post(
                    url,
                    auth=self._auth(),
                    headers=headers,
                    json=body or {},
                    timeout=self.timeout,
                )
        except requests.Timeout:
            raise ClientError(
                "timeout",
                f"Request to {path} timed out after {self.timeout}s",
                exit_code=EXIT_NETWORK,
            )
        except requests.RequestException as e:
            raise ClientError("network", str(e), exit_code=EXIT_NETWORK)

        request_id = resp.headers.get("x-ashby-request-id")

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            raise ClientError(
                "rate_limited",
                "Ashby rate limit exceeded (HTTP 429)",
                exit_code=EXIT_RATE_LIMITED,
                http_status=429,
                retryAfter=retry_after,
                requestId=request_id,
            )
        if resp.status_code >= 500:
            raise ClientError(
                "server_error",
                f"Ashby returned HTTP {resp.status_code}",
                exit_code=EXIT_NETWORK,
                http_status=resp.status_code,
                requestId=request_id,
                body=resp.text[:500],
            )
        if resp.status_code == 401 or resp.status_code == 403:
            try:
                payload = resp.json()
            except ValueError:
                payload = {"message": resp.text[:500]}
            return EnvelopeResult(
                ok=False,
                error={
                    "code": "unauthorized",
                    "message": payload.get("message") or payload.get("errorInfo", {}).get("message") or "Unauthorized",
                    "httpStatus": resp.status_code,
                    "requestId": request_id,
                },
                http_status=resp.status_code,
                request_id=request_id,
                exit_code=EXIT_API_ERROR,
            )

        try:
            payload = resp.json()
        except ValueError:
            raise ClientError(
                "invalid_json",
                "Ashby returned a non-JSON response",
                exit_code=EXIT_NETWORK,
                http_status=resp.status_code,
                requestId=request_id,
                body=resp.text[:500],
            )

        return self._envelope_from_payload(payload, resp.status_code, request_id)

    @staticmethod
    def _envelope_from_payload(payload: dict, http_status: int, request_id: str | None) -> EnvelopeResult:
        success = payload.get("success", False)
        if not success:
            err_info = payload.get("errorInfo")
            if err_info is None and "errors" in payload:
                raw = payload["errors"]
                if isinstance(raw, list):
                    err_info = {
                        "code": "api_error",
                        "message": "; ".join(str(e) for e in raw),
                        "errors": raw,
                    }
                elif isinstance(raw, dict):
                    err_info = raw
                else:
                    err_info = {"code": "api_error", "message": str(raw)}
            if err_info is None:
                err_info = {"code": "api_error", "message": "Ashby returned success=false with no errorInfo"}
            err_info = dict(err_info)
            err_info["httpStatus"] = http_status
            if request_id is not None:
                err_info["requestId"] = request_id
            return EnvelopeResult(
                ok=False,
                error=err_info,
                http_status=http_status,
                request_id=request_id,
                exit_code=EXIT_API_ERROR,
            )
        return EnvelopeResult(
            ok=True,
            data=payload.get("results"),
            more=payload.get("moreDataAvailable"),
            next_cursor=payload.get("nextCursor"),
            sync_token=payload.get("syncToken"),
            http_status=http_status,
            request_id=request_id,
            exit_code=EXIT_OK,
        )

    def paginate(
        self,
        path: str,
        body: dict,
        *,
        max_pages: int,
    ) -> Iterator[EnvelopeResult]:
        cursor = body.get("cursor")
        pages = 0
        while True:
            page_body = dict(body)
            if cursor:
                page_body["cursor"] = cursor
            result = self.post(path, page_body)
            yield result
            pages += 1
            if not result.ok:
                return
            if not result.more:
                return
            if pages >= max_pages:
                return
            if not result.next_cursor:
                return
            cursor = result.next_cursor
