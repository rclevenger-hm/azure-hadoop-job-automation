import json
import os
import re
import time
import uuid
from urllib.parse import urlsplit

from azure.cosmos import CosmosClient
from azure.identity import ManagedIdentityCredential
from azure.storage.queue import QueueClient

from app.auth import authenticate
from app.config import settings
from app.hdinsight import Hdinsight, Secrets
from app.service import Service, public
from app.store import Store
from app.validation import ApiError, STATES, body, integer

_SERVICE = None


def runtime():
    global _SERVICE
    if _SERVICE is None:
        cfg = settings()
        identity = ManagedIdentityCredential(client_id=os.environ['AZURE_CLIENT_ID'])
        db = CosmosClient(cfg['endpoint'], credential=identity, connection_timeout=3, request_timeout=8,
                          retry_total=2).get_database_client(cfg['database']).get_container_client(cfg['container'])
        queue = QueueClient.from_queue_url(cfg['queue_url'], credential=identity, retry_total=2, connection_timeout=3, read_timeout=8)
        store = Store(db, queue, cfg['daily_limit'], cfg['rate_limit'], cfg['retention'])
        _SERVICE = Service(store, Hdinsight(Secrets(identity), identity), cfg['profiles'])
    return _SERVICE
