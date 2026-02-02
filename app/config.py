import json
import os
import re
from urllib.parse import urlsplit

from app.auth import GUID


def prefix(value, azure_only=False):
    if not isinstance(value, str) or not value.endswith('/') or any(c in value for c in ['%', '\\', '*', '?', '#']) or any(ord(c) < 33 or ord(c) == 127 for c in value):
        raise ValueError('Use canonical directory prefixes ending in /')
    uri = urlsplit(value)
    if any(x in {'.', '..'} for x in uri.path.split('/')) or not uri.path.startswith('/'):
        raise ValueError('Invalid directory prefix')
    if uri.scheme in {'abfss', 'wasbs'}:
        endpoint = 'dfs' if uri.scheme == 'abfss' else 'blob'
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]@[a-z0-9]{3,24}\.' + endpoint + r'\.core\.windows\.net', uri.netloc):
            raise ValueError('Invalid Azure Storage URI')
    elif azure_only or uri.scheme != 'hdfs' or uri.netloc not in {'', 'namenode'}:
        raise ValueError('Use abfss, wasbs or hdfs:/// paths')
    return value


def load_profiles(raw):
    profiles = json.loads(raw)
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 5 or len(raw.encode()) > 16000:
        raise ValueError('Configure one to five profiles within 16 KiB')
    for name, p in profiles.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', name) or not isinstance(p, dict):
            raise ValueError('Invalid cluster profile')
        if not re.fullmatch(r'[a-z][a-z0-9-]{1,57}[a-z0-9]', p.get('cluster_name', '')):
            raise ValueError('Invalid HDInsight cluster name')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', p.get('username', '')):
            raise ValueError('Invalid HDInsight user')
        if not re.fullmatch(r'https://[a-zA-Z0-9-]{3,24}\.vault\.azure\.net/secrets/[a-zA-Z0-9-]{1,127}/[0-9a-f]{32}', p.get('secret_id', '')):
            raise ValueError('Use a version-pinned Key Vault secret ID')
        callers = p.get('allowed_callers', [])
        if not isinstance(callers, list) or not callers or any(not isinstance(a, str) or not re.fullmatch(GUID, a) for a in callers):
            raise ValueError('Use explicit Entra object IDs')
        for field in ['jar_prefixes', 'input_prefixes', 'output_prefixes']:
            values = p.get(field, [])
            if not isinstance(values, list) or not values:
                raise ValueError(f'Missing {field}')
            for value in values:
                prefix(value)
        prefix(p.get('status_prefix'), azure_only=True)
    return profiles


def settings():
    return {
        'profiles': load_profiles(os.environ['CLUSTER_PROFILES']),
        'endpoint': os.environ['COSMOS_ENDPOINT'], 'database': os.environ.get('COSMOS_DATABASE', 'hadoop'),
        'container': os.environ.get('COSMOS_CONTAINER', 'items'), 'queue_url': os.environ['JOB_QUEUE_URL'],
        'daily_limit': int(os.environ.get('DAILY_JOB_LIMIT', '100')),
        'rate_limit': int(os.environ.get('REQUESTS_PER_MINUTE', '60')),
        'retention': int(os.environ.get('RETENTION_DAYS', '30')),
    }
