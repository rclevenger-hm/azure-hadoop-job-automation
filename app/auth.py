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
