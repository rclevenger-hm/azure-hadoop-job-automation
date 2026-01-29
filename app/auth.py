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
