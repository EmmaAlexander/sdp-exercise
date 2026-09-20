"""Overall controll for observing, proessing, and review"""

import logging 
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path 

from sdp_control.models import Observation, ObservationState
from sdp_control.runner import run_observation, run_processing
from sdp_control.storage import storage_available, get_directory_size
from sdp_control.data_review import human_review

log = logging.getLogger(__name__)

DATA_DIR = Path("data")
STORAGE_THRESHOLD_BYTES = 5 * 1024**3 # 5GB
MAX_CONCURRENT_PROCESSING = 3

def handle_processing(obs: Observation) -> None:
	"""Process an observation and loop on review until accepted"""

	while True:
		image_prefix = DATA_DIR / f"{obs.obs_id}_image"
		run_processing(DATA_DIR, obs.visibility_path, image_prefix)
		obs.image_path = image_prefix 
		obs.transition_state(ObservationState.AWAITING_REVIEW)

		decision = human_review(obs)
		if decision == "continue":
			obs.visibility_path.unlink(missing_ok=True)
			obs.transition_state(ObservationState.DONE)
			break
		else:
			obs.transition_state(ObservationState.PROCESSING)

def main() -> None:
	"""Continually observe while storage allows and process each data set in parallel"""
	DATA_DIR.mkdir(exist_ok=True)

	with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PROCESSING) as executor:
		while True:
			current_size = get_directory_size(DATA_DIR)
			if not storage_available(current_size, STORAGE_THRESHOLD_BYTES):
				log.info("Storage threshold reached. Stopping new observations.")
				break

			obs = Observation()
			obs.transition_state(ObservationState.OBSERVING)
			vis_path = DATA_DIR / f"{obs.obs_id}.ms"
			run_observation(DATA_DIR, vis_path)
			obs.visibility_path = vis_path
			obs.transition_state(ObservationState.PROCESSING)

			executor.submit(handle_processing, obs)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	main()