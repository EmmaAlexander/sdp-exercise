"""Any QA tests needing to be done on the data"""

# TODO add in observign flags

import logging

from sdp_control.models import Observation

log = logging.getLogger(__name__)

DECISION_ALIASES = {
    "c": "continue",
    "continue": "continue",
    "r": "reprocess",
    "reprocess": "reprocess",
}


def human_review(obs: Observation) -> str:
    """Prompt a human for a quality decision, reprompting on invalid input."""
    while True:
        raw = input(
            f"Review {obs.obs_id} and image: {obs.image_path.name}. Decide to (c)ontinue or (r)eprocess? "
        ).strip().lower()

        if raw in DECISION_ALIASES:
            return DECISION_ALIASES[raw]

        log.warning(f"Unrecognised input '{raw}'. Please enter 'continue'/'c' or 'reprocess'/'r'")