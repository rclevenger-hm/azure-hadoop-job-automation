"""Atomic in-memory Cosmos subset. Tests also exercise SDK operation serialization."""
import copy
import re
from threading import RLock

from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError


