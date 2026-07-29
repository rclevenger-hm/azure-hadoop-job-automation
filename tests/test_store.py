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


def test_conflicting_key_does_not_consume_quota(env, payload):
    create(env, payload)
    payload['arguments'] = ['different']
    with pytest.raises(ApiError, match='different'):
        create(env, payload)
    assert env.store.usage(CALLER.tenant)['jobs'] == 1


def test_concurrent_same_key_only_admitted_once(env, payload):
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = list(pool.map(lambda _: create(env, payload), range(24)))
    assert len({j['submission_id'] for j in jobs}) == 1
    assert env.store.usage(CALLER.tenant)['jobs'] == 1
