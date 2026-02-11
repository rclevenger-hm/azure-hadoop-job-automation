import base64
import json
import time
import uuid
from datetime import datetime, timezone

from azure.core import MatchConditions
from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError

from app.validation import ApiError, TERMINAL, canonical, digest, identifier, invalid


class Store:
    def __init__(self, container, queue, daily_limit=100, rate_limit=60, retention=30, clock=time.time):
        self.items, self.queue = container, queue
        self.daily_limit, self.rate_limit, self.retention, self.clock = daily_limit, rate_limit, retention, clock
        if not all(isinstance(v, int) and v > 0 for v in [daily_limit, rate_limit, retention]):
            raise ValueError('Limits must be positive integers')

    def now(self):
        return int(self.clock())

    def date(self):
        return datetime.fromtimestamp(self.now(), timezone.utc).strftime('%Y-%m-%d')

    def read(self, tenant, id):
        try:
            return self.items.read_item(id, partition_key=tenant)
        except CosmosResourceNotFoundError:
            return None

    def get(self, tenant, job_id):
        item = self.read(tenant, job_id)
        return item if item and item.get('expires_at', self.now() + 1) > self.now() else None

    def enqueue(self, job):
        # Functions extension is configured for raw JSON, not its base64 default.
        self.queue.send_message(canonical({'tenant': job['tenant'], 'job_id': job['job_id']}), time_to_live=86400)

    def decorate(self, job):
        if job['status'] in TERMINAL:
            job.pop('active_shard', None)
            job['expires_at'] = self.now() + self.retention * 86400
            job['ttl'] = self.retention * 86400
        else:
            job.pop('expires_at', None)
            job['ttl'], job['active_shard'] = -1, job['job_id'][0]
        return job

    @staticmethod
    def conflict(exc):
        return getattr(exc, 'status_code', None) in {409, 412} or any(r.get('statusCode') in {409, 412} for r in getattr(exc, 'operation_responses', []))

    def create(self, tenant, job_id, request, profile):
        fingerprint, submission_id = digest(canonical(request)), uuid.uuid4().hex
        for _ in range(8):
            existing = self.read(tenant, job_id)
            if existing:
                if existing.get('expires_at', self.now() + 1) <= self.now():
                    raise ApiError(409, 'EXPIRED_KEY', 'Use a fresh idempotency key')
                if existing['fingerprint'] != fingerprint:
                    raise ApiError(409, 'IDEMPOTENCY_CONFLICT', 'Key already used with different job inputs')
                return existing, False
            counter_id = 'daily:' + self.date()
            usage = self.read(tenant, counter_id)
            units = (usage or {}).get('units', 0)
            if units >= self.daily_limit:
                raise ApiError(429, 'DAILY_LIMIT', 'Daily job allowance exhausted')
            job = self.decorate({'id': job_id, 'tenant': tenant, 'kind': 'job', 'job_id': job_id,
                                 'request': request, 'profile': profile, 'fingerprint': fingerprint,
                                 'submission_id': submission_id, 'statusdir': profile['status_prefix'] + submission_id,
                                 'status': 'QUEUED', 'version': 1, 'created_at': self.now(), 'updated_at': self.now(),
                                 'next_check': self.now() + 120})
            counter = {'id': counter_id, 'tenant': tenant, 'units': units + 1, 'ttl': 3 * 86400}
            operations = [('create', (job,)), self.counter_operation(counter, usage)]
            try:
                self.items.execute_item_batch(batch_operations=operations, partition_key=tenant)
                return self.read(tenant, job_id), True
            except (CosmosHttpResponseError, CosmosBatchOperationError) as exc:
                if not self.conflict(exc):
                    raise
        raise ApiError(409, 'STATE_CHANGED', 'Concurrent admission; retry with the same key')
