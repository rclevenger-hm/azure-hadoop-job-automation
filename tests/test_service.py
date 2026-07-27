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


def test_reconciliation_persists_page_and_matches(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMITTING', submitted_at=env.clock[0])
    env.clock[0] += 121
    env.backend.find.return_value = (['job_1780315200000_0003'], 'next')
    env.service.reconcile_one(job['tenant'], job['job_id'])
    first = env.store.get(job['tenant'], job['job_id'])
    assert first['scan_marker'] == 'next' and 'remote_id' not in first
    env.clock[0] += 31
    env.backend.find.return_value = (['job_1780315200000_0003'], '')
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['remote_id'] == 'job_1780315200000_0003'


def test_multiple_correlation_matches_require_review(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMITTING', submitted_at=env.clock[0])
    env.clock[0] += 121
    env.backend.find.return_value = (['job_1780315200000_0003', 'job_1780315200000_0004'], '')
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['reason'] == 'MULTIPLE_MATCHING_JOBS'


def test_queue_publish_failure_is_recoverable(env, payload, monkeypatch):
    original = env.store.enqueue
    monkeypatch.setattr(env.store, 'enqueue', lambda _: (_ for _ in ()).throw(RuntimeError('queue down')))
    with pytest.raises(RuntimeError):
        create(env, payload)
    jobs, _ = env.store.history(CALLER.tenant)
    assert len(jobs) == 1 and jobs[0]['status'] == 'QUEUED'
    monkeypatch.setattr(env.store, 'enqueue', original)
    env.clock[0] += 121
    env.service.reconcile_one(jobs[0]['tenant'], jobs[0]['job_id'])
    env.queue.send_message.assert_called()


def test_cancel_before_dispatch_prevents_execution(env, payload):
    job = create(env, payload)
    assert env.service.cancel(CALLER, job['job_id'])['status'] == 'CANCELLED'
    env.service.process(message(job))
    env.backend.submit.assert_not_called()
    assert env.service.cancel(CALLER, job['job_id'])['status'] == 'CANCELLED'


def test_cancellation_racing_submission_is_preserved(env, payload):
    job = create(env, payload)
    def submit(_):
        env.service.cancel(CALLER, job['job_id'])
        return 'job_1780315200000_0005'
    env.backend.submit.side_effect = submit
    env.service.process(message(job))
    current = env.store.get(job['tenant'], job['job_id'])
    assert current['status'] == 'CANCEL_REQUESTED' and current['remote_id'] == 'job_1780315200000_0005'
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.backend.cancel.assert_called_once()
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'CANCEL_REQUESTED'


def test_cancel_acknowledgment_is_not_terminal_cancellation(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.service.cancel(CALLER, job['job_id'])
    env.service.reconcile_one(job['tenant'], job['job_id'])
    current = env.store.get(job['tenant'], job['job_id'])
    assert current['cancel_accepted'] and current['status'] == 'CANCEL_REQUESTED'
    env.clock[0] += 121
    env.backend.status.return_value = 'SUCCEEDED'
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'SUCCEEDED'


def test_tenant_cannot_read_or_cancel_other_job(env, payload):
    job = create(env, payload)
    for action in [env.service.owned, env.service.cancel]:
        with pytest.raises(ApiError) as error:
            action(OTHER, job['job_id'])
        assert error.value.status == 404


def test_reconciler_respects_deadline(env, payload):
    create(env, payload)
    env.clock[0] += 121
    assert env.service.reconcile(lambda: 1000) == {'processed': 0, 'failed': 0}


def test_reconciler_counts_errors_and_continues(env, payload):
    job = create(env, payload)
    env.service.process(message(job))
    env.clock[0] += 121
    env.backend.status.side_effect = RuntimeError('api down')
    result = env.service.reconcile()
    assert result['failed'] == 1
    assert env.store.get(job['tenant'], job['job_id'])['next_check'] > env.clock[0]


def test_crash_before_remote_call_never_automatically_resubmits(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUBMITTING', submitted_at=env.clock[0])
    env.service.process(message(job))
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'SUBMISSION_UNKNOWN'
    env.backend.submit.assert_not_called()


def test_stale_queued_message_after_admission_expiry(env, payload):
    job = create(env, payload)
    env.clock[0] += 86401
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.service.process(message(job))
    env.backend.submit.assert_not_called()
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'FAILED'


def test_polling_never_rewrites_terminal_job(env, payload):
    job = create(env, payload)
    env.store.replace(job, status='SUCCEEDED')
    env.clock[0] += 121
    env.service.reconcile_one(job['tenant'], job['job_id'])
    env.backend.status.assert_not_called()


def test_expired_delivery_cannot_execute_before_recovery_runs(env, payload):
    job = create(env, payload)
    env.clock[0] += 86400
    env.service.process(message(job))
    env.backend.submit.assert_not_called()
    assert env.store.get(job['tenant'], job['job_id'])['status'] == 'FAILED'
