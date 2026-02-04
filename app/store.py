import base64
import json
import time
import uuid
from datetime import datetime, timezone

from azure.core import MatchConditions
from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError

from app.validation import ApiError, TERMINAL, canonical, digest, identifier, invalid


