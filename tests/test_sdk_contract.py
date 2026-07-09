"""Check Azure's actual serializers, not only the in-memory transaction model."""
from azure.cosmos._base import _format_batch_operations
from azure.storage.queue import QueueClient
from azure.core.credentials import AzureNamedKeyCredential

from app.store import Store


def test_sdk_serializes_compare_and_swap_batch():
    body = {'id': 'daily:2026-06-01', 'tenant': 'owner', 'units': 2, 'ttl': 259200}
    operation = Store.counter_operation(body, {'_etag':'expected'})
    result = _format_batch_operations([('create', ({'id':'job','tenant':'owner'},)), operation])
    assert result[0]['operationType'] == 'Create'
    assert result[1]['operationType'] == 'Replace'
    assert result[1]['ifMatch'] == 'expected'
    assert result[1]['resourceBody']['units'] == 2
