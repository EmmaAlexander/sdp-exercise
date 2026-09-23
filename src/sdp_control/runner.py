"""Run the external Docker-based SDP processing commands."""


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
    """Run an SDP processing script inside the Docker container.

    The command is executed as a subprocess with output captured for
    diagnostic logging. A non-zero exit status results in
    ``subprocess.CalledProcessError``.

    :param script: Name of the processing script to execute.
    :param args: Arguments passed to the processing script.
    :raises subprocess.CalledProcessError: If the Docker command fails.
    """
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
    """Acquire an observation using the SDP Docker environment.

    :param data_dir: Directory used to store observation data.
    :param visibility_path: Path where the generated visibility data is
        written.
    :raises subprocess.CalledProcessError: If observation acquisition fails.
    """

    _run_docker_script(
        data_dir,
        "/scripts/generate_visibilities.sh",
        f"/data/{output_path.name}",
        action="Starting observation",
    )


def run_processing(data_dir: Path, visibilities_path: Path, output_prefix: Path) -> None:
    """Process an observation using the SDP Docker environment.

    :param data_dir: Directory containing the observation data.
    :param visibility_path: Path to the visibility data to process.
    :param image_path: Directory where processed image data is written.
    :raises subprocess.CalledProcessError: If processing fails.
    """

    _run_docker_script(
        data_dir,
        "/scripts/process_visibilities.sh",
        f"/data/{visibilities_path.name}",
        f"/data/{output_prefix.name}",
        action="Processing",
    )
