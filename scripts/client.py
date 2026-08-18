"""Small Azure CLI credential client. Never print access tokens."""
import argparse
import json
import uuid
from urllib.parse import urlsplit

import requests
from azure.identity import AzureCliCredential


