"""Configuration for the control system, loaded from environment variables.

Values can be overridden via a .env file in the project root (see
.env.example) or real environment variables, which take precedence over
the .env file. Falls back to sensible defaults if unset.
"""

import os
from pathlib import Path

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "data")).resolve()
STORAGE_THRESHOLD_BYTES: int = int(os.environ.get("STORAGE_THRESHOLD_BYTES", 5 * 1024**3))
MAX_CONCURRENT_PROCESSING: int = int(os.environ.get("MAX_CONCURRENT_PROCESSING", 3))