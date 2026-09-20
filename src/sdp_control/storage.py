"""Storage threshold checking for the control system"""

from pathlib import Path 

def get_directory_size(path: Path) -> int:
	"""Return the total size in bytes of all files in given directory"""

	if not path.exists():
		return 0
		# to do: add warning message here about path not existing?
	
	total_size = 0
	for entry in path.rglob("*"):
		if entry.is_file():
			total_size += entry.stat().st_size

	return total_size

def storage_available(current_size_bytes: int, threshold_bytes: int) -> bool:
	"""Check if there is enough storage available to start a new observation."""
	return current_size_bytes < threshold_bytes