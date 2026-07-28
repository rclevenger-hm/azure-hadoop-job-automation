import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.validation import ApiError, key_id
from conftest import CALLER, OTHER, create


