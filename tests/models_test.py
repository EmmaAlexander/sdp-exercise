"""Tests for the models.py"""

import pytest

from sdp_control.models import Observation, ObservationState


def test_new_observation_defaults_to_pending():
    obs = Observation()

    assert obs.state == ObservationState.PENDING


def test_transition_state():
    obs = Observation(state=ObservationState.PENDING)

    obs.transition_state(ObservationState.OBSERVING)

    assert obs.state == ObservationState.OBSERVING


def test_invalid_transition_raises_error():
    obs = Observation(state=ObservationState.PENDING)

    with pytest.raises(ValueError, match="PENDING -> DONE"):
        obs.transition_state(ObservationState.DONE)


@pytest.mark.parametrize(
    "terminal_state",
    [ObservationState.DONE, ObservationState.FAILED],
)
def test_terminal_states_cannot_transition(terminal_state):
    obs = Observation(state=terminal_state)

    with pytest.raises(ValueError):
        obs.transition_state(ObservationState.PROCESSING)
