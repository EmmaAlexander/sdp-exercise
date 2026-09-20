"""Overall controll for observing, proessing, and review"""

import logging 
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path 

from sdp_control.models import Observation, ObservationState
from sdp_control.runner import run_observation, run_processing
from sdp_control.storage import storage_available, get_directory_size

log = logging.getLogger(__name__)

DATA_DIR = Path("data")
STORAGE_THRESHOLD_BYTES = 5 * 1024**3 # 5GB
MAX_CONCURRENT_PROCESSING = 3
