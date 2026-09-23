"""Data models and state management for SDP observations.

Defines the lifecycle states of an observation and enforces valid
transitions between those states.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from uuid import uuid4

log = logging.getLogger(__name__)


class ObservationState(Enum):
    """The stages of an observation as it moves through the control system pipeline."""

    PENDING = auto()
    OBSERVING = auto()
    PROCESSING = auto()
    AWAITING_REVIEW = auto()
    DONE = auto()
    FAILED = auto()

# Define valid state transitions for an observation
VALID_TRANSITIONS = {
    ObservationState.PENDING: {
        ObservationState.OBSERVING,
    },
    ObservationState.OBSERVING: {
        ObservationState.PROCESSING,
        ObservationState.FAILED,
    },
    ObservationState.PROCESSING: {
        ObservationState.AWAITING_REVIEW,
        ObservationState.FAILED,
    },
    ObservationState.AWAITING_REVIEW: {
        ObservationState.PROCESSING,
        ObservationState.DONE,
        ObservationState.FAILED,
    },
    ObservationState.DONE: set(),
    ObservationState.FAILED: set(),
}


@dataclass
class Observation:
    """Represent a single SDP observation and its processing state.

    An observation progresses through a fixed lifecycle from acquisition
    through processing and human review. State changes should be made via
    :meth:`transition_state` so that invalid lifecycle transitions are
    rejected.

    :param obs_id: Unique identifier for the observation.
    :param visibility_path: Path to the raw visibility data.
    :param image_path: Path to the processed image, if available.
    :param state: Current lifecycle state of the observation.
    """

    obs_id: str = field(default_factory=lambda: str(uuid4()))
    state: ObservationState = ObservationState.PENDING
    visibility_path: Path | None = None
    image_path: Path | None = None
    created_at: datetime = field(default_factory=datetime.now)
    stage_durations: dict[str, float] = field(default_factory=dict)
    _stage_started_at: datetime = field(default_factory=datetime.now, repr=False)

    def transition_state(self, new_state: ObservationState) -> None:
        """Transition the observation to a new lifecycle state.

        The requested transition is checked against :data:`VALID_TRANSITIONS`.
        Invalid transitions raise ``ValueError``.

        :param new_state: State to transition the observation into.
        :raises ValueError: If the requested transition is not valid.
        """

        if new_state not in VALID_TRANSITIONS[self.state]:
            raise ValueError(f"Invalid state transition: {self.state.name} -> {new_state.name}")

        elapsed = (datetime.now() - self._stage_started_at).total_seconds()
        self.stage_durations[self.state.name] = elapsed

        log.info(
            f"Observation {self.obs_id}: {self.state.name} -> {new_state.name} "
            f"(after {elapsed:.1f}s)"
        )

        self.state = new_state
        self._stage_started_at = datetime.now()
