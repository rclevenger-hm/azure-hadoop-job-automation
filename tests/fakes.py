"""Atomic in-memory Cosmos subset. Tests also exercise SDK operation serialization."""
import copy
import re
from threading import RLock

from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError


class Container:
    def __init__(self):
        self.data, self.lock, self.sequence = {}, RLock(), 0
