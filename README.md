# SDP mock control system

A small control system that automates a long observation campaign. 
It continually "observes" while storage allows, processes observations concurrently, and allows for human QA input.

## Requirements: 
- Python 3.10+
- Docker (daemon must be running — `docker ps` should succeed)
- Poetry for dependency management

## Installation 

```bash
git clone https://github.com/EmmaAlexander/sdp-exercise.git
cd sdp-exercise
poetry install
```

## Configuration

Set via environment variables; defaults shown below.

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `data` | Where observation data is stored |
| `STORAGE_THRESHOLD_BYTES` | `1073741824` | Stop new observations once storage usage reaches this |
| `MAX_CONCURRENT_PROCESSING` | `3` | Maximum observations processed concurrently |

## Running

```bash
poetry run python -m sdp_control.controller
```

## Testing

```bash
poetry run pytest -v
```