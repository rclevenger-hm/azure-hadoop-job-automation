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
