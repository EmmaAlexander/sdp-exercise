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

    def transition_state(self, new_state: ObservationState) -> None:
        """Move the observation to a valid next state."""
        if new_state not in VALID_TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid state transition: "
                f"{self.state.name} -> {new_state.name}"
            )

        log.info(
            "Observation %s: %s -> %s",
            self.obs_id,
            self.state.name,
            new_state.name,
        )
        self.state = new_state