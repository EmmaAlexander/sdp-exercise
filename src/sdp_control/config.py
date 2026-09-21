"""Configuration for the control system.

Values are read from environment variables and fall back to sensible
defaults when they are not set.
"""

import os
from pathlib import Path

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "data")).resolve()
STORAGE_THRESHOLD_BYTES: int = int(os.environ.get("STORAGE_THRESHOLD_BYTES", 1 * 1024**3))
MAX_CONCURRENT_PROCESSING: int = int(os.environ.get("MAX_CONCURRENT_PROCESSING", 3))
