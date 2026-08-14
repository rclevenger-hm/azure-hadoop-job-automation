"""Create a reproducible, explicit allowlist of Azure Functions source files."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


