import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
import requests
from azure.core.exceptions import ResourceNotFoundError

from app.hdinsight import Hdinsight, RemoteMismatch, Secrets
from app.validation import ApiError
from conftest import create, remote


@pytest.fixture
def native():
    session = MagicMock(spec=requests.Session)
    secret = Mock()
    secret.password.return_value = 'never-log-password'
    return Hdinsight(secret, session=session)


def reply(native, value, status=200):
    response = native.session.request.return_value.__enter__.return_value
    response.status_code = status
    response.iter_content.return_value = [json.dumps(value).encode()]
    return response


def test_real_requests_form_preserves_argument_boundaries(native, env, payload):
    payload['arguments'] = ['two words', '$(touch /tmp/owned)', 'a&b=c']
    job = create(env, payload)
    reply(native, {'id': 'job_123_0001'})
    assert native.submit(job) == 'job_123_0001'
    args, kw = native.session.request.call_args
    prepared = requests.Request(args[0], args[1], params=kw['params'], data=kw['data']).prepare()
    from urllib.parse import parse_qs
    form = parse_qs(prepared.body)
    assert form['arg'] == native.arguments(job)
    assert form['statusdir'] == [job['statusdir']]
    assert prepared.url.endswith('?user.name=admin')
    assert kw['allow_redirects'] is False and kw['timeout'] == (3, 8)
    assert kw['auth'] == ('admin', 'never-log-password')
    native.session.mount.assert_called_once()


@pytest.mark.parametrize('status', [301, 302, 400, 401, 404, 429, 500, 503])
def test_non_success_never_retried(native, env, payload, status):
    reply(native, {}, status)
    with pytest.raises(RuntimeError):
        native.submit(create(env, payload))
    native.session.request.assert_called_once()


@pytest.mark.parametrize('id', ['http://evil', 'job_1_2/../../x', 'wrong', None])
def test_ambiguous_submission_identity(native, env, payload, id):
    reply(native, {'id': id})
    with pytest.raises(RemoteMismatch):
        native.submit(create(env, payload))


def test_response_size_and_error_envelopes(native, env, payload):
    job = create(env, payload)
    response = reply(native, {})
    response.iter_content.return_value = [b'x' * (1024 * 1024 + 1)]
    with pytest.raises(RuntimeError):
        native.submit(job)
    reply(native, {'error': 'sensitive internals'})
    with pytest.raises(RuntimeError, match='reported an error'):
        native.submit(job)


@pytest.mark.parametrize('field,value', [('jar', 'different'), ('class', 'different'), ('arg', ['different']), ('statusdir', 'different')])
def test_remote_provenance_requires_entire_request(native, env, payload, field, value):
    job = create(env, payload)
    result = remote(job)
    result['userargs'][field] = value
    with pytest.raises(RemoteMismatch):
        native.verify(job, result, result['id'])


def test_cancel_checks_provenance_before_delete(native, env, payload):
    job = create(env, payload)
    job['remote_id'] = 'job_123_0001'
    native.call = Mock(return_value=remote(job, id='job_999_0001'))
    with pytest.raises(RemoteMismatch):
        native.cancel(job)
    assert native.call.call_count == 1
    assert native.call.call_args.args[1] == 'GET'


def test_find_checks_exact_status_directory_and_all_inputs(native, env, payload):
    job = create(env, payload)
    unrelated = remote(job, id='job_123_0001')
    unrelated['userargs']['statusdir'] = 'unrelated'
    matched = remote(job, id='job_123_0002')
    native.call = Mock(side_effect=[[{'id': unrelated['id']}, {'id': matched['id']}], unrelated, matched])
    assert native.find(job) == ([matched['id']], '')


def test_full_page_retains_scan_marker_and_previous_matches(native, env, payload):
    job = create(env, payload)
    job['scan_matches'] = ['job_123_0000']
    ids = [f'job_123_000{i}' for i in range(1, 6)]
    native.call = Mock(side_effect=[[{'id': id} for id in ids], *[{'userargs': {}} for _ in ids]])
    assert native.find(job) == (['job_123_0000'], ids[-1])


def test_remote_page_must_progress(native, env, payload):
    job = create(env, payload)
    job['scan_marker'] = 'job_123_0002'
    native.call = Mock(return_value=[{'id': 'job_123_0001'}])
    with pytest.raises(RemoteMismatch):
        native.find(job)


@pytest.mark.parametrize('state,exit_value,want', [('PREP', None, 'SUBMITTED'), ('RUNNING', None, 'RUNNING'), ('SUCCEEDED', None, 'RUNNING'), ('SUCCEEDED', 0, 'SUCCEEDED'), ('SUCCEEDED', 2, 'FAILED'), ('FAILED', None, 'FAILED'), ('KILLED', None, 'CANCELLED')])
def test_launcher_and_child_exit_state(native, env, payload, state, exit_value, want):
    assert native.state(remote(create(env, payload), state=state, exit_value=exit_value)) == want


def test_numeric_state_and_unknown_states(native):
    assert native.state({'status': {'runState': 2}, 'exitValue': 0}) == 'SUCCEEDED'
    with pytest.raises(RuntimeError):
        native.state({'status': {'state': 'NEW_UNKNOWN'}})
