"""Check Azure's actual serializers, not only the in-memory transaction model."""
from azure.cosmos._base import _format_batch_operations
from azure.storage.queue import QueueClient
from azure.core.credentials import AzureNamedKeyCredential

from app.store import Store


