import json
import re
import time
from functools import lru_cache
from urllib.parse import urlsplit

import requests
from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

from app.validation import ApiError

JOB_ID = r'job_[0-9]{1,24}_[0-9]{1,12}'
MAX_RESPONSE = 1024 * 1024


class RemoteMismatch(Exception):
    pass


def remote_id(value):
    if not isinstance(value, str) or not re.fullmatch(JOB_ID, value):
        raise RemoteMismatch('Invalid remote job identity')
    return value


class Secrets:
    def __init__(self, credential):
        self.credential = credential

    @lru_cache(maxsize=16)
    def password(self, id):
        uri = urlsplit(id)
        _, _, name, version = uri.path.split('/')
        with SecretClient(f'https://{uri.netloc}', self.credential, retry_total=2, connection_timeout=3, read_timeout=8) as client:
            value = client.get_secret(name, version).value
        if not value:
            raise RuntimeError('Empty cluster credential')
        return value


class Hdinsight:
    def __init__(self, secrets, credential=None, session=None, blob_factory=None):
        self.secrets, self.credential = secrets, credential
        self.session = session or requests.Session()
        # Requests defaults to zero transport retries; explicitly retain that contract.
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
        self.session.trust_env = False
        self.blob_factory = blob_factory or self.blobs

    def blobs(self, account):
        return BlobServiceClient(f'https://{account}.blob.core.windows.net', credential=self.credential,
                                 retry_total=2, connection_timeout=3, read_timeout=8)

    def call(self, job, method, path, params=None, data=None):
        p = job['profile']
        url = f"https://{p['cluster_name']}.azurehdinsight.net/templeton/v1/{path}"
        started = time.monotonic()
        with self.session.request(method, url, params={'user.name': p['username'], **(params or {})}, data=data,
                                  auth=(p['username'], self.secrets.password(p['secret_id'])),
                                  timeout=(3, 8), allow_redirects=False, stream=True) as response:
            if response.status_code < 200 or response.status_code >= 300:
                raise RuntimeError('HDInsight request failed')
            raw = bytearray()
            for chunk in response.iter_content(8192):
                raw.extend(chunk)
                if len(raw) > MAX_RESPONSE or time.monotonic() - started > 25:
                    raise RuntimeError('HDInsight response exceeded limits')
            result = json.loads(raw)
            if isinstance(result, dict) and ('error' in result or 'errorCode' in result):
                raise RuntimeError('HDInsight reported an error')
            return result

    @staticmethod
    def arguments(job):
        r = job['request']
        return [r['input_path'], r['output_path'], *r['arguments']]

    def submit(self, job):
        r = job['request']
        form = [('jar', r['jar_path']), ('class', r['job_class']), ('statusdir', job['statusdir']), ('enablelog', 'false')]
        form.extend(('arg', value) for value in self.arguments(job))
        # There is no native idempotency token. The durable SUBMITTING state precedes this one POST.
        result = self.call(job, 'POST', 'mapreduce/jar', data=form)
        return remote_id(result.get('id'))

    def verify(self, job, result, expected):
        r, args = job['request'], result.get('userargs', {})
        if (result.get('id') != expected or result.get('user') != job['profile']['username']
                or args.get('statusdir') != job['statusdir'] or args.get('jar') != r['jar_path']
                or args.get('class') != r['job_class'] or args.get('arg') != self.arguments(job)):
            raise RemoteMismatch('Remote job does not match the durable submission')
        return result

    def get(self, job, id):
        return self.verify(job, self.call(job, 'GET', 'jobs/' + remote_id(id)), id)

    def find(self, job):
        params = {'numrecords': 5}
        marker = job.get('scan_marker')
        if marker:
            params['jobid'] = remote_id(marker)
        rows = self.call(job, 'GET', 'jobs', params=params)
        if not isinstance(rows, list) or len(rows) > 5:
            raise RemoteMismatch('Invalid remote page')
        ids = [remote_id(row.get('id')) for row in rows]
        if ids != sorted(set(ids)) or (marker and any(id <= marker for id in ids)):
            raise RemoteMismatch('Non-progressing remote page')
        found = set(job.get('scan_matches', []))
        for id in ids:
            result = self.call(job, 'GET', 'jobs/' + id)
            if result.get('userargs', {}).get('statusdir') == job['statusdir']:
                self.verify(job, result, id)
                found.add(id)
        return sorted(found), ids[-1] if len(ids) == 5 else ''

    @staticmethod
    def state(result):
        status = result.get('status', {})
        state = status.get('state') or {1: 'RUNNING', 2: 'SUCCEEDED', 3: 'FAILED', 4: 'PREP', 5: 'KILLED'}.get(status.get('runState'))
        if state == 'SUCCEEDED':
            # WebHCat's launcher completion alone does not prove hadoop jar succeeded.
            code = result.get('exitValue')
            return 'RUNNING' if code is None else 'SUCCEEDED' if type(code) is int and code == 0 else 'FAILED'
        mapped = {'PREP': 'SUBMITTED', 'RUNNING': 'RUNNING', 'FAILED': 'FAILED', 'KILLED': 'CANCELLED'}
        if state not in mapped:
            raise RuntimeError('Unrecognized HDInsight state')
        return mapped[state]

    def status(self, job):
        return self.state(self.get(job, job['remote_id']))

    def cancel(self, job):
        self.get(job, job['remote_id'])  # Recheck provenance before acting on the remote ID.
        result = self.call(job, 'DELETE', 'jobs/' + remote_id(job['remote_id']))
        return result.get('id') == job['remote_id']

    def logs(self, job, stream, limit):
        if stream not in {'stdout', 'stderr', 'exit'}:
            raise ApiError(400, 'INVALID_STREAM', 'stream must be stdout, stderr or exit')
        if not job.get('remote_id'):
            raise ApiError(409, 'NOT_SUBMITTED', 'No remote job has been identified yet')
        uri = urlsplit(job['statusdir'])
        container, host = uri.netloc.split('@')
        account = host.split('.')[0]
        key = uri.path.lstrip('/') + '/' + stream
        try:
            with self.blob_factory(account) as client:
                blob = client.get_blob_client(container, key)
                size = blob.get_blob_properties().size
                raw = b'' if size == 0 else blob.download_blob(offset=0, length=min(size, limit + 1), max_concurrency=1).readall()
        except ResourceNotFoundError as exc:
            raise ApiError(404, 'LOG_NOT_READY', 'WebHCat has not written this log yet') from exc
        return {'stream': stream, 'text': raw[:limit].decode('utf-8', errors='replace'), 'truncated': size > limit,
                'limit_bytes': limit, 'note': 'Beginning of the launcher log; uploads may lag execution.'}
