import re
from dataclasses import dataclass
from functools import lru_cache

import jwt

from app.validation import ApiError, digest

GUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


@dataclass(frozen=True)
class Identity:
    directory: str
    subject: str

    @property
    def tenant(self):
        return digest(f'{self.directory}:{self.subject}')


@lru_cache(maxsize=1)
def keys(directory):
    if not re.fullmatch(GUID, directory):
        raise ValueError('Invalid tenant ID')
    return jwt.PyJWKClient(f'https://login.microsoftonline.com/{directory}/discovery/v2.0/keys', cache_keys=True, lifespan=300, timeout=5)


def authenticate(header, directory, audience, allowed, key_client=None):
    try:
        if not isinstance(header, str) or not header.startswith('Bearer ') or len(header) > 16384:
            raise ValueError()
        token = header[7:]
        key = (key_client or keys(directory)).get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=['RS256'], audience=audience,
                            issuer=f'https://login.microsoftonline.com/{directory}/v2.0',
                            options={'require': ['exp', 'iat', 'nbf', 'sub', 'oid', 'tid', 'iss', 'aud']})
        if claims['tid'] != directory or claims.get('ver') != '2.0' or not re.fullmatch(GUID, claims['oid']) or claims['oid'] not in allowed:
            raise ValueError()
        return Identity(directory, claims['oid'])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise ApiError(401, 'UNAUTHENTICATED', 'An authorized Microsoft Entra v2 access token is required') from exc
