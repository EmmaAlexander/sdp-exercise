"""Wrappers around the mock observae and process Docker commands."""

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

IMAGE = "docker.io/pw410/ska-sdp-mock:0.1"


def run_observation(data_dir: Path, output_path: Path) -> None:
    """Generate mock visibility data from an observation with Docker."""
    log.info(f"Starting observation -> {output_path}")
    result = subprocess.run(
        [
            "docker", "run", "-v", f"{data_dir}:/data",
            IMAGE, "/scripts/generate_visibilities.sh", f"/data/{output_path.name}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Observation failed:\n{result.stdout}\n{result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, result.args)


def run_processing(data_dir: Path, visibilities_path: Path, output_prefix: Path) -> None:
    """Image visibility data with Docker."""
    log.info(f"Processing {visibilities_path.name} -> {output_prefix.name}")
    result = subprocess.run(
        [
            "docker", "run", "-v", f"{data_dir}:/data",
            IMAGE, "/scripts/process_visibilities.sh",
            f"/data/{visibilities_path.name}", f"/data/{output_prefix.name}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error(f"Processing failed:\n{result.stdout}\n{result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, result.args)