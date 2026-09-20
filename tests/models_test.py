"""Tests for the models.py"""

from sdp_control.models import Observation, ObservationState

def test_transition_state():
	obs = Observation()
	assert obs.state == ObservationState.PENDING

	obs.transition_state(ObservationState.OBSERVING)

	assert obs.state == ObservationState.OBSERVING