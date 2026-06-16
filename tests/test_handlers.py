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


def test_api_submit_replay_history_usage_and_status(api, payload):
    first, status, headers = api('POST', '/jobs', payload)
    assert status == 202 and headers['Cache-Control'] == 'no-store'
    assert api('POST', '/jobs', payload)[1] == 200
    assert api('GET', '/jobs')[0]['jobs'] == [first]
    assert api('GET', '/jobs/' + first['job_id'])[0] == first
    assert api('GET', '/usage')[0]['jobs'] == 1


def test_cancel_and_log_routes(api, env, payload):
    job = create(env, payload)
    assert api('POST', f"/jobs/{job['job_id']}/cancel")[0]['status'] == 'CANCELLED'
    env.backend.logs.return_value = {'text': 'bounded'}
    assert api('GET', f"/jobs/{job['job_id']}/logs", query={'stream': 'stderr', 'limit': '20'})[0] == {'text': 'bounded'}


@pytest.mark.parametrize('method,path,query,status', [('GET', '/bad', {}, 404), ('GET', '/jobs', {'limit':'0'}, 400), ('GET', '/jobs', {'status':'BAD'}, 400), ('GET', '/jobs/no', {}, 400)])
def test_bad_routes_and_queries(api, method, path, query, status):
    assert api(method, path, query=query)[1] == status


def test_content_type_and_body_limit(api, payload):
    assert api('POST', '/jobs', payload, headers={'Content-Type':'text/plain'})[1] == 415
    assert api('POST', '/jobs', {'huge':'x'*65537})[1] == 413


def test_internal_error_redaction(api, env, capsys):
    env.store.request_limit = lambda _: (_ for _ in ()).throw(RuntimeError('password=secret'))
    result, status, _ = api('GET', '/usage')
    assert status == 503 and 'secret' not in json.dumps(result) + capsys.readouterr().out


def test_authentication_runs_before_database(api, env, monkeypatch):
    monkeypatch.setattr(handlers, 'authenticate', lambda *a: (_ for _ in ()).throw(ApiError(401, 'UNAUTHENTICATED', 'Denied')))
    assert api('GET', '/usage')[1] == 401
    assert env.db.data == {}


def test_worker_redelivery_and_reconciliation(api, env, payload):
    job = create(env, payload)
    raw = json.dumps(message(job)).encode()
    handlers.worker_handler(raw)
    handlers.worker_handler(raw)
    env.backend.submit.assert_called_once()
    env.clock[0] += 121
    assert handlers.reconcile_handler()['processed'] == 1


@pytest.mark.parametrize('raw', [b'[]', b'{}', b'x'*1025, b'{"tenant":"bad","job_id":"bad"}'])
def test_malformed_queue_message_is_not_acknowledged(api, raw):
    with pytest.raises((ValueError, ApiError)):
        handlers.worker_handler(raw)
