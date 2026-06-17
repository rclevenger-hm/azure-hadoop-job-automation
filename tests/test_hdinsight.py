import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
import requests
from azure.core.exceptions import ResourceNotFoundError

from app.hdinsight import Hdinsight, RemoteMismatch, Secrets
from app.validation import ApiError
from conftest import create, remote


