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


def test_crashed_submitter_reconciles_by_exact_name(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMITTING', submitted_at=env.clock[0])
    env.clock[0] += 121
    env.backend.find.return_value = (['job_1780315200000_0002'], '')
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['remote_id'] == 'job_1780315200000_0002'
    env.backend.submit.assert_not_called()


def test_missing_remote_step_requires_review_without_retry(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMISSION_UNKNOWN', submitted_at=env.clock[0])
    env.clock[0] += 86401
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'NEEDS_REVIEW'
    env.backend.submit.assert_not_called()
