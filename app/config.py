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
