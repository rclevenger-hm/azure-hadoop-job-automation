import copy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.auth import Identity
from app.config import load_profiles
from app.hdinsight import Hdinsight
from app.service import Service
from app.store import Store
from fakes import Container

CALLER = Identity('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111')
OTHER = Identity(CALLER.directory, '33333333-3333-3333-3333-333333333333')


