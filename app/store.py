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
