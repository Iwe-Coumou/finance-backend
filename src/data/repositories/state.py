from src.logging import get_logger
import json
from pathlib import Path

_logger = get_logger(__name__)

def _read() -> dict:
    try:
        with open(Path("state.json"), 'r') as f:
            data = json.load(f)
            _logger.debug("State file read successfully")
            return data
    except FileNotFoundError:
        _logger.debug("State file does not exist, returning empty state")
        return {}

def _write(state: dict) -> None:
    with open(Path("state.json"), 'w') as f:
        json.dump(state, f, indent=2)
    _logger.debug("State file written successfully")

def get(key: str, default=None):
    data = _read()
    value = data.get(key, default)
    if value is None:
        _logger.debug(f"Key not found in state | key={key}")
    else:
        _logger.info(f"State get | key={key} value={value}")
    return value

def set(key: str, value) -> None:
    data = _read()
    if key in data:
        _logger.warning(f"Key already exists in state, overwriting | key={key}")
    data[key] = value
    _write(data)
    _logger.info(f"State set | key={key} value={value}")

def update(key: str, value) -> None:
    data = _read()
    if key not in data:
        _logger.warning(f"Key not found in state, cannot update | key={key}")
        return
    data[key] = value
    _write(data)
    _logger.info(f"State updated | key={key} value={value}")