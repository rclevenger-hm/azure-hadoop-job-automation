import time
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import authenticate
from app.validation import ApiError
from conftest import CALLER

AUDIENCE = '44444444-4444-4444-4444-444444444444'


@pytest.fixture(scope='module')
def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def claims():
    now = int(time.time())
    return {'iss': f'https://login.microsoftonline.com/{CALLER.directory}/v2.0', 'aud': AUDIENCE, 'tid': CALLER.directory,
            'oid': CALLER.subject, 'sub': 'opaque-subject', 'ver': '2.0', 'iat': now, 'nbf': now - 1, 'exp': now + 300}


def verify(key, values, signing_key=None, algorithm='RS256'):
    token = jwt.encode(values, signing_key or key, algorithm=algorithm)
    client = Mock()
    client.get_signing_key_from_jwt.return_value = SimpleNamespace(key=key.public_key())
    return authenticate('Bearer ' + token, CALLER.directory, AUDIENCE, [CALLER.subject], client)


def test_valid_cryptographically_signed_access_token(key):
    assert verify(key, claims()) == CALLER


@pytest.mark.parametrize('field,value', [('aud', 'other'), ('iss', 'https://evil/'), ('tid', 'other'), ('oid', '33333333-3333-3333-3333-333333333333'), ('exp', 1), ('nbf', 9999999999), ('ver', '1.0')])
def test_invalid_claims_rejected(key, field, value):
    data = claims()
    data[field] = value
    with pytest.raises(ApiError) as error:
        verify(key, data)
    assert error.value.status == 401
