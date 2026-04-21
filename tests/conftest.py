import os

import pytest


@pytest.fixture(autouse=True)
def _default_api_key(monkeypatch):
    monkeypatch.setenv("ASHBY_API_KEY", "test-key")
