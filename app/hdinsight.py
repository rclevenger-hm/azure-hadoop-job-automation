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
