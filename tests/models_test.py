"""Tests for the models.py"""

from sdp_control.models import Observation, ObservationState

def test_new_observation_defaults_to_pending():
    obs = Observation()

    assert obs.state == ObservationState.PENDING


def test_transition_state():
    obs = Observation(state=ObservationState.PENDING)

    obs.transition_state(ObservationState.OBSERVING)

    assert obs.state == ObservationState.OBSERVING