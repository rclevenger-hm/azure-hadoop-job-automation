import hashlib
import json
import re
from urllib.parse import urlsplit

MAX_BODY = 65536
TERMINAL = frozenset({'SUCCEEDED', 'FAILED', 'CANCELLED', 'NEEDS_REVIEW'})
STATES = TERMINAL | {'QUEUED', 'SUBMITTING', 'SUBMISSION_UNKNOWN', 'SUBMITTED', 'RUNNING', 'CANCEL_REQUESTED'}


