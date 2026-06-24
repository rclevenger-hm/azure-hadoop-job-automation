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
