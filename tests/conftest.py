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


@pytest.fixture
def profiles():
    return load_profiles(open('examples/profiles.json').read())


@pytest.fixture
def payload():
    return json.load(open('examples/job.json'))


@pytest.fixture
def env(profiles):
    db, queue, backend = Container(), Mock(), Mock()
    clock = [1780315200]
    store = Store(db, queue, clock=lambda: clock[0])
    backend.submit.return_value = 'job_1780315200000_0001'
    backend.find.return_value = ([], '')
    backend.status.return_value = 'RUNNING'
    backend.cancel.return_value = True
    service = Service(store, backend, copy.deepcopy(profiles))
    return SimpleNamespace(store=store, service=service, backend=backend, clock=clock, db=db, queue=queue)
