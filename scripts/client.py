"""Small Azure CLI credential client. Never print access tokens."""
import argparse
import json
import uuid
from urllib.parse import urlsplit

import requests
from azure.identity import AzureCliCredential


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--scope', required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    submit = commands.add_parser('submit')
    submit.add_argument('file')
    submit.add_argument('--key', default=None, help='Reuse the SAME key for ambiguous API retries')
    for name in ['status', 'cancel', 'logs']:
        command = commands.add_parser(name)
        command.add_argument('job_id')
        if name == 'logs':
            command.add_argument('--stream', choices=['stdout', 'stderr', 'exit'], default='stdout')
    commands.add_parser('history')
    commands.add_parser('usage')
    args = parser.parse_args()
    uri = urlsplit(args.url)
    if uri.scheme != 'https' or uri.username or uri.password or uri.query or uri.fragment or uri.path not in {'', '/'}:
        parser.error('--url must be an HTTPS origin')
    headers = {'Authorization': 'Bearer ' + AzureCliCredential().get_token(args.scope).token}
    method, path, data, query = 'GET', '/jobs', None, None
    if args.command == 'submit':
        method, data = 'POST', json.load(open(args.file))
        headers['Idempotency-Key'] = args.key or uuid.uuid4().hex
        print('Idempotency-Key:', headers['Idempotency-Key'])
    elif args.command in {'status', 'cancel', 'logs'}:
        if len(args.job_id) != 64 or any(c not in '0123456789abcdef' for c in args.job_id):
            parser.error('job_id must be 64 lowercase hex characters')
        path = '/jobs/' + args.job_id
        if args.command == 'cancel':
            method, path = 'POST', path + '/cancel'
        elif args.command == 'logs':
            path, query = path + '/logs', {'stream': args.stream}
    elif args.command == 'usage':
        path = '/usage'
    response = requests.request(method, args.url.rstrip('/') + path, headers=headers, json=data, params=query, timeout=(5, 30), allow_redirects=False)
    print(response.status_code, response.text)
    if response.status_code >= 300:
        raise SystemExit(1)
