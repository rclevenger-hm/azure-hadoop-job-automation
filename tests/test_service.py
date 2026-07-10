import pytest
from app.validation import ApiError
from conftest import CALLER, OTHER
from conftest import create


def message(job):
    return {'tenant': job['tenant'], 'job_id': job['job_id']}
