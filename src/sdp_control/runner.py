"""Wrappers around the mock observe and process Docker commands."""

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

IMAGE = "docker.io/pw410/ska-sdp-mock:0.1"


def _run_docker_script(
    data_dir: Path,
    script: str,
    *args: str,
    action: str,
) -> None:
    """Run a mock pipeline script in Docker, raising on failure."""
    log.info("%s -> %s", action, args[-1])

    result = subprocess.run(
        ["docker", "run", "-v", f"{data_dir}:/data", IMAGE, script, *args],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log.error(
            "%s failed:\n%s\n%s",
            action,
            result.stdout,
            result.stderr,
        )
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )


def run_observation(data_dir: Path, output_path: Path) -> None:
    """Generate mock visibility data from an observation with Docker."""
    _run_docker_script(
        data_dir, "/scripts/generate_visibilities.sh",
        f"/data/{output_path.name}",
        action="Starting observation",
    )


def run_processing(data_dir: Path, visibilities_path: Path, output_prefix: Path) -> None:
    """Image visibility data with Docker."""
    _run_docker_script(
        data_dir, "/scripts/process_visibilities.sh",
        f"/data/{visibilities_path.name}", f"/data/{output_prefix.name}",
        action="Processing",
    )