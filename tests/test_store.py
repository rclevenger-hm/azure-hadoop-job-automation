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


def test_daily_quota_atomic_under_competing_keys(env, payload):
    env.store.daily_limit = 3
    def submit(i):
        try:
            return create(env, payload, f'unique-key-{i}')
        except ApiError:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(submit, range(24)))
    assert sum(r is not None for r in results) == 3
    assert env.store.usage(CALLER.tenant)['jobs'] == 3


def test_compare_and_swap_does_not_lose_cancellation(env, payload):
    old = create(env, payload)
    env.store.replace(old, status='CANCELLED', cancel_requested=True)
    assert env.store.replace(old, status='SUBMITTING') is None


def test_active_jobs_never_expire_automatically(env, payload):
    job = create(env, payload)
    assert job['ttl'] == -1 and 'expires_at' not in job
    env.clock[0] += 365 * 86400
    assert env.store.get(CALLER.tenant, job['job_id'])


def test_terminal_ttl_and_expired_key(env, payload):
    job = create(env, payload)
    result = env.store.replace(job, status='SUCCEEDED')
    assert result['ttl'] == 30 * 86400 and 'active_shard' not in result
    env.clock[0] += 30 * 86400
    assert env.store.get(CALLER.tenant, job['job_id']) is None
    with pytest.raises(ApiError, match='fresh'):
        create(env, payload)


def test_request_rate_and_daily_counters_separate(env, payload):
    env.store.rate_limit = 2
    env.store.request_limit(CALLER.tenant)
    env.store.request_limit(CALLER.tenant)
    with pytest.raises(ApiError) as e:
        env.store.request_limit(CALLER.tenant)
    assert e.value.status == 429
    assert env.store.usage(CALLER.tenant)['jobs'] == 0
    env.clock[0] += 60
    env.store.request_limit(CALLER.tenant)


def test_utc_day_resets_allowance(env, payload):
    create(env, payload)
    env.clock[0] += 86400
    assert env.store.usage(CALLER.tenant)['jobs'] == 0


def test_queue_only_carries_opaque_ids(env, payload):
    job = create(env, payload)
    args, kwargs = env.queue.send_message.call_args
    assert json.loads(args[0]) == {'tenant': job['tenant'], 'job_id': job['job_id']}
    assert kwargs == {'time_to_live': 86400}


def test_history_cursor_is_scoped_and_no_equal_time_duplicates(env, payload):
    for i in range(7):
        create(env, payload, f'page-key-{i}')
    first, cursor = env.store.history(CALLER.tenant, limit=3)
    second, next_cursor = env.store.history(CALLER.tenant, limit=3, cursor=cursor)
    third, end = env.store.history(CALLER.tenant, limit=3, cursor=next_cursor)
    assert len({j['id'] for j in first + second + third}) == 7 and end is None
    for tenant, status in [(OTHER.tenant, None), (CALLER.tenant, 'RUNNING')]:
        with pytest.raises(ApiError):
            env.store.history(tenant, cursor=cursor, status=status)
