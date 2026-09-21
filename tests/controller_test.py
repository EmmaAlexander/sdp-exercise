"""Tests processing in controller.py"""

from pathlib import Path
from unittest.mock import Mock, patch

from sdp_control import controller
from sdp_control.models import Observation, ObservationState


def make_observation(**overrides) -> Observation:
    """Build an Observation with sensible test defaults, overridable per test."""
    defaults = dict(
        visibility_path=Path("data/abc123.ms"),
        image_path=None,
        state=ObservationState.PROCESSING,
    )
    defaults.update(overrides)
    return Observation(**defaults)


def test_process_transitions_and_queues():
    obs = make_observation()
    state = controller.CampaignState()

    with patch("sdp_control.controller.run_processing") as mock_run:
        controller.process_and_queue(obs, state)

    mock_run.assert_called_once()
    assert obs.state == ObservationState.AWAITING_REVIEW
    assert obs.image_path is not None
    assert state.review_queue.get_nowait() is obs


def test_submit_calls_executor():
    obs = make_observation()
    state = controller.CampaignState()
    executor = Mock()

    controller.submit_processing(obs, executor, state)

    executor.submit.assert_called_once_with(controller.process_and_queue, obs, state)


def test_submit_marks_failed_on_processing_failure():
    obs = make_observation()
    state = controller.CampaignState()
    state.mark_pending(obs)
    executor = Mock()
    future = Mock()
    executor.submit.return_value = future

    controller.submit_processing(obs, executor, state)

    on_done = future.add_done_callback.call_args[0][0]
    future.result.side_effect = RuntimeError("docker exploded")
    on_done(future)

    assert obs.state == ObservationState.FAILED
    assert obs.obs_id not in state.pending


def test_submit_keeps_pending_on_success():
    obs = make_observation()
    state = controller.CampaignState()
    state.mark_pending(obs)
    executor = Mock()
    future = Mock()
    executor.submit.return_value = future

    controller.submit_processing(obs, executor, state)
    on_done = future.add_done_callback.call_args[0][0]
    future.result.return_value = None
    on_done(future)

    assert obs.obs_id in state.pending


def test_review_continue_deletes_and_completes():
    obs = make_observation(image_path=Path("data/abc123_image"), state=ObservationState.AWAITING_REVIEW)
    state = controller.CampaignState()
    state.mark_pending(obs)
    state.review_queue.put(obs)
    state.review_queue.put(None)
    executor = Mock()

    with patch("sdp_control.controller.human_review", return_value="continue"), \
         patch("sdp_control.controller.shutil.rmtree") as mock_rmtree, \
         patch.object(Path, "exists", return_value=True):
        controller.reviewer_loop(executor, state)

    mock_rmtree.assert_called_once_with(obs.visibility_path)
    assert obs.state == ObservationState.DONE
    assert obs.obs_id not in state.pending
    executor.submit.assert_not_called()


def test_review_reprocess_resubmits():
    obs = make_observation(image_path=Path("data/abc123_image"), state=ObservationState.AWAITING_REVIEW)
    state = controller.CampaignState()
    state.mark_pending(obs)
    state.review_queue.put(obs)
    state.review_queue.put(None)
    executor = Mock()

    with patch("sdp_control.controller.human_review", return_value="reprocess"), \
         patch("sdp_control.controller.shutil.rmtree") as mock_rmtree:
        controller.reviewer_loop(executor, state)

    mock_rmtree.assert_not_called()
    assert obs.state == ObservationState.PROCESSING
    assert obs.obs_id in state.pending
    executor.submit.assert_called_once_with(controller.process_and_queue, obs, state)


def test_shutdown_completes_when_nothing_pending():
    state = controller.CampaignState()
    executor = Mock()
    reviewer_thread = Mock()

    controller.shutdown(executor, reviewer_thread, state)

    assert state.observing_finished.is_set()
    assert state.campaign_complete.is_set()
    executor.shutdown.assert_called_once_with(wait=True)
    reviewer_thread.join.assert_called_once()
    assert state.review_queue.get_nowait() is None

def test_review_failure_marks_observation_failed():
    obs = make_observation(
        image_path=Path("data/abc123_image"),
        state=ObservationState.AWAITING_REVIEW,
    )
    state = controller.CampaignState()
    state.mark_pending(obs)
    state.review_queue.put(obs)
    state.review_queue.put(None)

    executor = Mock()

    with patch(
        "sdp_control.controller.human_review",
        side_effect=RuntimeError("review failed"),
    ):
        controller.reviewer_loop(executor, state)

    assert obs.state == ObservationState.FAILED
    assert obs.obs_id not in state.pending

def test_review_cleanup_failure_marks_observation_failed():
    obs = make_observation(
        image_path=Path("data/abc123_image"),
        state=ObservationState.AWAITING_REVIEW,
    )
    state = controller.CampaignState()
    state.mark_pending(obs)
    state.review_queue.put(obs)
    state.review_queue.put(None)

    executor = Mock()

    with patch(
        "sdp_control.controller.human_review",
        return_value="continue",
    ), patch(
        "sdp_control.controller.shutil.rmtree",
        side_effect=OSError("could not remove visibility data"),
    ), patch.object(
        Path,
        "exists",
        return_value=True,
    ):
        controller.reviewer_loop(executor, state)

    assert obs.state == ObservationState.FAILED
    assert obs.obs_id not in state.pending



def test_main_stops_when_storage_threshold_reached():
    with patch(
        "sdp_control.controller.get_directory_size",
        return_value=100,
    ), patch(
        "sdp_control.controller.storage_available",
        return_value=False,
    ), patch(
        "sdp_control.controller.run_observation",
    ) as mock_run_observation, patch(
        "sdp_control.controller.ThreadPoolExecutor",
    ) as mock_executor_class, patch(
        "sdp_control.controller.threading.Thread",
    ) as mock_thread_class:

        mock_executor = mock_executor_class.return_value
        mock_reviewer_thread = mock_thread_class.return_value

        controller.main()

    mock_run_observation.assert_not_called()
    mock_executor.shutdown.assert_called_once_with(wait=True)
    mock_reviewer_thread.start.assert_called_once()
    mock_reviewer_thread.join.assert_called_once()