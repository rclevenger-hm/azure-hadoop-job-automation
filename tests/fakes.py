"""Atomic in-memory Cosmos subset. Tests also exercise SDK operation serialization."""
import copy
import re
from threading import RLock

from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError


class Container:
    def __init__(self):
        self.data, self.lock, self.sequence = {}, RLock(), 0

    def read_item(self, id, partition_key):
        with self.lock:
            value = self.data.get((partition_key, id))
            if value is None:
                raise CosmosResourceNotFoundError(status_code=404)
            return copy.deepcopy(value)

    def stamp(self, body):
        self.sequence += 1
        return {**copy.deepcopy(body), '_etag': str(self.sequence)}

    def execute_item_batch(self, batch_operations, partition_key):
        with self.lock:
            pending = copy.deepcopy(self.data)
            results = []
            for index, operation in enumerate(batch_operations):
                kind, args, *options = operation
                body = args[-1]
                assert body['tenant'] == partition_key
                key = (partition_key, body['id'])
                previous = pending.get(key)
                code = 409 if kind == 'create' and previous else 412 if kind == 'replace' and (not previous or options[0]['if_match_etag'] != previous['_etag']) else None
                if code:
                    raise CosmosBatchOperationError(index, status_code=code, operation_responses=[{'statusCode': code}])
                assert kind in {'create', 'replace'}
                pending[key] = self.stamp(body)
                results.append({'statusCode': 201, 'resourceBody': pending[key]})
            self.data = pending
            return copy.deepcopy(results)

    def replace_item(self, id, body, etag, match_condition):
        with self.lock:
            key = (body['tenant'], id)
            previous = self.data.get(key)
            if not previous or previous['_etag'] != etag:
                raise CosmosHttpResponseError(status_code=412)
            self.data[key] = self.stamp(body)
            return copy.deepcopy(self.data[key])
