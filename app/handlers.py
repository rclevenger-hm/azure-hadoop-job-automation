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


