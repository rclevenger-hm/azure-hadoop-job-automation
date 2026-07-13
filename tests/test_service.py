import pytest
from app.validation import ApiError
from conftest import CALLER, OTHER
from conftest import create


def message(job):
    return {'tenant': job['tenant'], 'job_id': job['job_id']}


def test_duplicate_deliveries_submit_once(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.process(message(job))
    env.backend.submit.assert_called_once()
    assert env.store.get(job['tenant'], job['job_id'])['remote_id'] == 'job_1780315200000_0001'


def test_timeout_after_start_becomes_unknown_never_resubmits(env, payload):
    job = create(env, payload)
    env.backend.submit.side_effect = TimeoutError('sensitive detail')
    env.service.process(message(job))
    env.service.process(message(job))
    current = env.store.get(job['tenant'], job['job_id'])
    assert current['status'] == 'SUBMISSION_UNKNOWN'
    assert current['reason'] == 'SUBMISSION_OUTCOME_UNKNOWN'
    env.backend.submit.assert_called_once()
