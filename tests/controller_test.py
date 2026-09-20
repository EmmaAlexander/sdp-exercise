"""Tests processing in controller.py"""

import queue
from pathlib import Path 
from unittest.mock import Mock, patch

from sdp_control import controller
from sdp_control.models import Observation, ObservationState

def test_process_and_queue():
	obs= Observation(visibility_path=Path("data/abc123.ms"))
	executor=Mock()

	with patch("sdp_control.controller.run_processing") as mock_run_processing, \
		patch("sdp_control.controller.review_queue",queue.Queue()) as mock_queue:

		controller.process_and_queue(obs,executor)

		mock_run_processing.assert_called_once()
		assert obs.state == ObservationState.AWAITING_REVIEW
		assert obs.image_path == controller.DATA_DIR / f"{obs.obs_id}_image"

		queued_obs = mock_queue.get_nowait()
		assert queued_obs is obs

def test_reviewer_loop_continue_deletes_and_marks_done():
	obs = Observation(
		visibility_path=Path("data/abc123.ms"),
		image_path=Path("data/abc123_image"),
		state=ObservationState.AWAITING_REVIEW
	)
	test_queue = queue.Queue()
	test_queue.put(obs)
	test_queue.put(None) # sentinal to stop the loop

	executor = Mock()

	with patch("sdp_control.controller.review_queue", test_queue), \
		patch("sdp_control.controller.human_review", return_value="continue"), \
		patch("sdp_control.controller.shutil.rmtree") as mock_rmtree, \
		patch("sdp_control.controller._mark_done") as mock_mark_done, \
		patch.object(Path, "exists", return_value=True):

		controller.reviewer_loop(executor)

	mock_rmtree.assert_called_once_with(obs.visibility_path)
	mock_mark_done.assert_called_once()
	assert obs.state == ObservationState.DONE 
	executor.submit.assert_not_called()

def test_reviewer_loop_reprocess_resubmits_without_deleting():
	obs = Observation(
		visibility_path=Path("data/abc123.ms"),
		image_path=Path("data/abc123_image"),
		state=ObservationState.AWAITING_REVIEW,
	)
	test_queue = queue.Queue()
	test_queue.put(obs)
	test_queue.put(None)

	executor = Mock()

	with patch("sdp_control.controller.review_queue", test_queue), \
		patch("sdp_control.controller.human_review", return_value="reprocess"), \
		patch("sdp_control.controller.shutil.rmtree") as mock_rmtree, \
		patch("sdp_control.controller._mark_done") as mock_mark_done:

		controller.reviewer_loop(executor)

	mock_rmtree.assert_not_called()
	mock_mark_done.assert_not_called()
	assert obs.state == ObservationState.PROCESSING
	executor.submit.assert_called_once_with(controller.process_and_queue, obs, executor)
