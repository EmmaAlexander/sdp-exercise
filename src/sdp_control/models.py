"""Core data models for SDP"""

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
    """A single observation at any point in the pipeline."""

    obs_id: str = field(default_factory=lambda: str(uuid4()))
    state: ObservationState = ObservationState.PENDING
    visibility_path: Path | None = None
    image_path: Path | None = None
    created_at: datetime = field(default_factory=datetime.now)
    stage_durations: dict[str, float] = field(default_factory=dict)
    _stage_started_at: datetime = field(default_factory=datetime.now, repr=False)

    def transition_state(self, new_state: ObservationState) -> None:
        """Move the observation to a valid next state."""
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
