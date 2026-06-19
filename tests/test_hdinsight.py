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
