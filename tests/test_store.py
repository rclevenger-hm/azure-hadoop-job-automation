import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.validation import ApiError, key_id
from conftest import CALLER, OTHER, create


def test_admission_is_idempotent_and_counts_once(env, payload):
    first = create(env, payload)
    second = create(env, payload)
    assert first == second
    assert env.store.usage(CALLER.tenant)['jobs'] == 1
