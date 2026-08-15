import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.auth import Identity  # noqa: E402
from app.config import load_profiles  # noqa: E402
from app.validation import STATES, job_request  # noqa: E402


