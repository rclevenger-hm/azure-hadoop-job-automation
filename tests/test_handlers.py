import importlib
import json
import sys

import azure.functions as func
import pytest

from app import handlers
from app.validation import ApiError
from conftest import CALLER, create, message


@pytest.fixture
def api(env, monkeypatch):
    monkeypatch.setattr(handlers, '_SERVICE', env.service)
    monkeypatch.setattr(handlers, 'authenticate', lambda *a: CALLER)
    monkeypatch.setenv('ENTRA_TENANT_ID', CALLER.directory)
    monkeypatch.setenv('TOKEN_AUDIENCE', 'audience')
    monkeypatch.setenv('ALLOWED_CALLER_IDS', CALLER.subject)
    def call(method, path, payload=None, query=None, headers=None):
        request = func.HttpRequest(method, 'https://test.azurewebsites.net' + path, params=query or {}, headers={
            'Authorization': 'Bearer example', 'Content-Type': 'application/json', 'Idempotency-Key': 'api-key-123', **(headers or {})},
            body=json.dumps(payload).encode() if payload is not None else b'')
        value, status, response_headers = handlers.api_handler(request)
        return json.loads(value), status, response_headers
    return call
