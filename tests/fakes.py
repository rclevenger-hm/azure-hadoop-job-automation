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
