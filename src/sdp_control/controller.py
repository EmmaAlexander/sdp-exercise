"""Overall controll for observing, proessing, and review"""

from __future__ import annotations

import logging
import queue
import shutil
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from sdp_control.data_review import human_review
from sdp_control.models import Observation, ObservationState
from sdp_control.runner import run_observation, run_processing
from sdp_control.storage import get_directory_size, storage_available

from sdp_control.config import DATA_DIR, MAX_CONCURRENT_PROCESSING, STORAGE_THRESHOLD_BYTES

log = logging.getLogger(__name__)
status = logging.getLogger("status")


@dataclass
class CampaignState:
    """Shared coordination state for one running campaign."""

    review_queue: queue.Queue[Observation | None] = field(default_factory=queue.Queue)
    pending: set[str] = field(default_factory=set)
    pending_lock: threading.Lock = field(default_factory=threading.Lock)
    observing_finished: threading.Event = field(default_factory=threading.Event)
    campaign_complete: threading.Event = field(default_factory=threading.Event)

    def mark_pending(self, obs: Observation) -> None:
        """Record that an observation is now in flight (processing or review)."""
        with self.pending_lock:
            self.pending.add(obs.obs_id)

    def mark_complete(self, obs: Observation) -> None:
        """Record that an observation has finished, and check if the campaign is done."""
        with self.pending_lock:
            self.pending.discard(obs.obs_id)
            if not self.pending and self.observing_finished.is_set():
                self.campaign_complete.set()


def process_and_queue(obs: Observation, state: CampaignState) -> None:
    """Process an observation, then queue it for human review."""
    if obs.visibility_path is None:
        raise ValueError(
            f"Observation {obs.obs_id} has no visibility data to process"
        )
    image_prefix = DATA_DIR / f"{obs.obs_id}_image"
    run_processing(DATA_DIR, obs.visibility_path, image_prefix)
    obs.image_path = image_prefix
    obs.transition_state(ObservationState.AWAITING_REVIEW)
    state.review_queue.put(obs)
    status.info(f"Observation {obs.obs_id[:8]} ready for review")


def submit_processing(obs: Observation, executor: ThreadPoolExecutor, state: CampaignState) -> None:
    """Submit an observation to the processing pool, handling failures via callback."""

    def on_done(future: Future[None]) -> None:
        try:
            future.result()
        except Exception:
            log.exception(f"Processing failed for observation {obs.obs_id}")
            obs.transition_state(ObservationState.FAILED)
            state.mark_complete(obs)

    future = executor.submit(process_and_queue, obs, state)
    future.add_done_callback(on_done)


def reviewer_loop(executor: ThreadPoolExecutor, state: CampaignState) -> None:
    """Review processed observations one at a time until the queue is closed."""
    while True:
        obs = state.review_queue.get()

        if obs is None:
            return

        try:
            decision = human_review(obs)

            if decision == "continue":
                if obs.visibility_path and obs.visibility_path.exists():
                    shutil.rmtree(obs.visibility_path)

                obs.transition_state(ObservationState.DONE)
                state.mark_complete(obs)
                status.info(
                    f"Observation {obs.obs_id[:8]} accepted, "
                    "visibility data removed"
                )
            else:  # "reprocess"
                obs.transition_state(ObservationState.PROCESSING)
                submit_processing(obs, executor, state)

        except Exception:
            log.exception(
                "Review failed for observation %s",
                obs.obs_id,
            )
            obs.transition_state(ObservationState.FAILED)
            state.mark_complete(obs)



def shutdown(executor: ThreadPoolExecutor, reviewer_thread: threading.Thread, state: CampaignState) -> None:
    """Signal that observing has finished, and wait for everything else to drain."""
    state.observing_finished.set()

    with state.pending_lock:
        if not state.pending:
            state.campaign_complete.set()

    log.info("Observing finished; waiting for processing and review to finish.")
    state.campaign_complete.wait()

    state.review_queue.put(None)
    reviewer_thread.join()
    executor.shutdown(wait=True)
    log.info("Campaign complete.")
    status.info("Campaign complete.")


def main() -> None:
    """Run observations until the storage threshold is reached."""
    DATA_DIR.mkdir(exist_ok=True)

    state = CampaignState()
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PROCESSING)
    reviewer_thread = threading.Thread(target=reviewer_loop, args=(executor, state))
    reviewer_thread.start()

    observations_started = 0

    try:
        while True:
            current_size = get_directory_size(DATA_DIR)
            if not storage_available(current_size, STORAGE_THRESHOLD_BYTES):
                if observations_started == 0:
                    status.info(
                        f"No observations were run: existing data ({current_size} bytes) "
                        f"already meets or exceeds the storage threshold "
                        f"({STORAGE_THRESHOLD_BYTES} bytes)."
                    )

                else:
                    log.info("Storage threshold reached; stopping new observations.")
                break

            obs = Observation()
            obs.transition_state(ObservationState.OBSERVING)
            status.info(f"Observing {obs.obs_id[:8]}...")
            visibility_path = DATA_DIR / f"{obs.obs_id}.ms"
            run_observation(DATA_DIR, visibility_path)
            obs.visibility_path = visibility_path
            obs.transition_state(ObservationState.PROCESSING)

            state.mark_pending(obs)
            submit_processing(obs, executor, state)
            observations_started += 1
    finally:
        shutdown(executor, reviewer_thread, state)


if __name__ == "__main__":
    logging.basicConfig(
        filename="campaign.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger("status").addHandler(console_handler)

    main()
