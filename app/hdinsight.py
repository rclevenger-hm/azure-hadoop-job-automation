import json
import re
import time
from functools import lru_cache
from urllib.parse import urlsplit

import requests
from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

from app.validation import ApiError

JOB_ID = r'job_[0-9]{1,24}_[0-9]{1,12}'
MAX_RESPONSE = 1024 * 1024


class RemoteMismatch(Exception):
    pass


def remote_id(value):
    if not isinstance(value, str) or not re.fullmatch(JOB_ID, value):
        raise RemoteMismatch('Invalid remote job identity')
    return value


class Secrets:
    def __init__(self, credential):
        self.credential = credential

    @lru_cache(maxsize=16)
    def password(self, id):
        uri = urlsplit(id)
        _, _, name, version = uri.path.split('/')
        with SecretClient(f'https://{uri.netloc}', self.credential, retry_total=2, connection_timeout=3, read_timeout=8) as client:
            value = client.get_secret(name, version).value
        if not value:
            raise RuntimeError('Empty cluster credential')
        return value


class Hdinsight:
    def __init__(self, secrets, credential=None, session=None, blob_factory=None):
        self.secrets, self.credential = secrets, credential
        self.session = session or requests.Session()
        # Requests defaults to zero transport retries; explicitly retain that contract.
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
        self.session.trust_env = False
        self.blob_factory = blob_factory or self.blobs
