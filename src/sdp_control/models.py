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


@dataclass
class Observation:
    """A single observation at any point in the pipeline."""

    obs_id: str = field(default_factory=lambda: str(uuid4()))
    state: ObservationState = ObservationState.PENDING
    visibility_path: Path | None = None
    image_path: Path | None = None

    def transition_state(self, new_state: ObservationState) -> None:
        """Move observation to a new state and record the change."""
        log.info(f"Observation {self.obs_id}: {self.state.name} -> {new_state.name}")
        self.state = new_state