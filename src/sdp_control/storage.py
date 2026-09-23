"""Utilities for monitoring campaign storage usage."""

from pathlib import Path


def get_directory_size(path: Path) -> int:
    """Calculate the total size of files in a directory.

    :param path: Directory whose contents should be measured.
    :return: Total size in bytes.
    """

    if not path.exists():
        return 0

    total_size = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total_size += entry.stat().st_size

    return total_size


def storage_available(current_size_bytes: int, threshold_bytes: int) -> bool:
    """Check whether storage usage is below the configured threshold.

    :param current_size_bytes: Current storage usage in bytes.
    :param threshold_bytes: Maximum permitted storage usage in bytes.
    :return: ``True`` if storage usage is below the threshold, otherwise
        ``False``.
    """

    return current_size_bytes < threshold_bytes
