"""Overall controll for observing, proessing, and review"""

import logging 
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path 
import shutil
import queue 
import threading

from sdp_control.models import Observation, ObservationState
from sdp_control.runner import run_observation, run_processing
from sdp_control.storage import storage_available, get_directory_size
from sdp_control.data_review import human_review

log = logging.getLogger(__name__)

DATA_DIR = Path("data").resolve()
STORAGE_THRESHOLD_BYTES = 5 * 1024**3 # 5GB
MAX_CONCURRENT_PROCESSING = 1

review_queue: queue.Queue = queue.Queue()

_pending_lock=threading.Lock()
_pending_count=0
_observing_finished = threading.Event()
_campaign_complete = threading.Event()


def _mark_pending() -> None:
	"""Record that one more observation is processing or in review"""
	global _pending_count
	with _pending_lock:
		_pending_count +=1

def _mark_done() -> None:
	"""Record that an obsevation has reached DONE and check if campaign is finished"""
	global _pending_count 
	with _pending_lock:
		_pending_count -= 1
		remaining = _pending_count

	if remaining == 0 and _observing_finished.is_set():
		_campaign_complete.set()

def process_and_queue(obs: Observation, executor: ThreadPoolExecutor) -> None:
	"""Run processing for an observation then queue for qa review"""
	image_prefix = DATA_DIR / f"{obs.obs_id}_image"
	run_processing(DATA_DIR, obs.visibility_path, image_prefix)
	obs.image_path = image_prefix
	obs.transition_state(ObservationState.AWAITING_REVIEW)
	review_queue.put(obs)

def reviewer_loop(executor: ThreadPoolExecutor) -> None:
	"""Review observations one by one from the queue"""
	while True:
		obs = review_queue.get()
		if obs is None:
			break

		decision = human_review(obs)
		if decision == "continue":
			if obs.visibility_path and obs.visibility_path.exists():
				shutil.rmtree(obs.visibility_path)
			obs.transition_state(ObservationState.DONE)
			_mark_done()
		else:
			obs.transition_state(ObservationState.PROCESSING)
			executor.submit(process_and_queue, obs, executor)

def main() -> None:

	"""Observe continuously while storage allows, process and review in background"""
	DATA_DIR.mkdir(exist_ok=True)

	executor= ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PROCESSING)
	reviewer_thread = threading.Thread(target=reviewer_loop, args = (executor,))
	reviewer_thread.start()

	while True:
		current_size= get_directory_size(DATA_DIR)
		if not storage_available(current_size,STORAGE_THRESHOLD_BYTES):
			log.info("Storage threashold reached. Stopping new observations.")
			break

		obs = Observation()
		obs.transition_state(ObservationState.OBSERVING)
		vis_path= DATA_DIR / f"{obs.obs_id}.ms"
		run_observation(DATA_DIR, vis_path)
		obs.visibility_path = vis_path
		obs.transition_state(ObservationState.PROCESSING)

		_mark_pending()
		executor.submit(process_and_queue, obs, executor)

	_observing_finished.set()
	if _pending_count==0:
		_campaign_complete.set()

	log.info("Waiting for remaining processing and review to finish")

	_campaign_complete.wait()

	executor.shutdown(wait=True)
	review_queue.put(None)
	reviewer_thread.join()

	log.info("Everything complete")




if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	main()