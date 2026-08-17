import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.auth import Identity  # noqa: E402
from app.config import load_profiles  # noqa: E402
from app.validation import STATES, job_request  # noqa: E402


def main():
    profiles = load_profiles((ROOT / 'examples/profiles.json').read_text())
    payload = json.loads((ROOT / 'examples/job.json').read_text())
    job_request(payload, profiles, Identity('22222222-2222-2222-2222-222222222222', profiles['analytics']['allowed_callers'][0]))
    api = yaml.safe_load((ROOT / 'openapi.yaml').read_text())
    assert set(api['paths']) == {'/jobs', '/jobs/{job_id}', '/jobs/{job_id}/cancel', '/jobs/{job_id}/logs', '/usage'}
    assert set(api['components']['schemas']['Job']['properties']['status']['enum']) == STATES
    host = json.loads((ROOT / 'host.json').read_text())
    assert host['extensions']['queues']['messageEncoding'] == 'none'
    assert host['extensions']['http']['routePrefix'] == ''
    assert not any('..' in str(p) for p in (ROOT / 'app').glob('*.py'))
    print('API, examples and trigger contracts agree.')
