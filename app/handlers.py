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


def response(status, value, request_id):
    return json.dumps(value), status, {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Request-Id': request_id,
                                     **({'Retry-After': '60'} if status == 429 else {})}


def api_handler(request):
    request_id, status = str(uuid.uuid4()), 500
    try:
        caller = authenticate(request.headers.get('Authorization'), os.environ['ENTRA_TENANT_ID'], os.environ['TOKEN_AUDIENCE'], os.environ['ALLOWED_CALLER_IDS'].split(','))
        service = runtime()
        service.store.request_limit(caller.tenant)
        method, path, query = request.method, urlsplit(request.url).path.rstrip('/') or '/', request.params
        match = re.fullmatch(r'/jobs/([^/]+)(?:/(cancel|logs))?', path)
        result, status = None, 200
        if method == 'POST' and path == '/jobs':
            if request.headers.get('Content-Type', '').split(';')[0].lower() != 'application/json':
                raise ApiError(415, 'UNSUPPORTED_MEDIA_TYPE', 'Use application/json')
            result, created = service.submit(caller, request.headers.get('Idempotency-Key'), body(request.get_body()))
            status = 202 if created else 200
        elif method == 'GET' and path == '/jobs':
            if query.get('status') and query['status'] not in STATES:
                raise ApiError(400, 'INVALID_STATUS', 'Unknown job status')
            jobs, cursor = service.store.history(caller.tenant, integer(query.get('limit'), 20, 100), query.get('cursor'), query.get('status'))
            result = {'jobs': [public(j) for j in jobs], 'next_cursor': cursor}
        elif method == 'GET' and match and not match[2]:
            result = public(service.owned(caller, match[1]))
        elif method == 'POST' and match and match[2] == 'cancel':
            result = service.cancel(caller, match[1])
            status = 202 if result['status'] == 'CANCEL_REQUESTED' else 200
        elif method == 'GET' and match and match[2] == 'logs':
            result = service.backend.logs(service.owned(caller, match[1]), query.get('stream', 'stdout'), integer(query.get('limit'), 16384, 65536))
        elif method == 'GET' and path == '/usage':
            result = service.store.usage(caller.tenant)
        else:
            raise ApiError(404, 'NOT_FOUND', 'Route not found')
        return response(status, result, request_id)
    except ApiError as exc:
        status = exc.status
        result = response(status, {'code': exc.code, 'error': str(exc), 'request_id': request_id}, request_id)
        if exc.code == 'DAILY_LIMIT':
            result[2]['Retry-After'] = str(86400 - int(time.time()) % 86400)
        return result
    except Exception as exc:
        status = 503
        print(json.dumps({'event': 'api_error', 'request_id': request_id, 'error_type': type(exc).__name__}), flush=True)
        return response(status, {'code': 'SERVICE_UNAVAILABLE', 'error': 'Service temporarily unavailable', 'request_id': request_id}, request_id)
    finally:
        print(json.dumps({'event': 'api_request', 'request_id': request_id, 'status': status}), flush=True)


def worker_handler(raw):
    if len(raw) > 1024:
        raise ValueError('Invalid queue message')
    message = body(raw)
    if set(message) != {'tenant', 'job_id'}:
        raise ValueError('Invalid queue message')
    runtime().process(message)
