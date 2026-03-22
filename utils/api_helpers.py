from __future__ import annotations

from datetime import datetime
from typing import Any


def clean_nan_values(value: Any) -> Any:
    """Recursively replace NaN values with None for JSON-safe responses."""
    if isinstance(value, float):
        return None if value != value else value
    if isinstance(value, dict):
        return {key: clean_nan_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_nan_values(item) for item in value]
    return value


def current_timestamp() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def success_response(*, clean_nan: bool = False, **payload: Any) -> dict[str, Any]:
    response = {'status': 'success', **payload}
    return clean_nan_values(response) if clean_nan else response


def status_message_response(success: bool, success_message: str, error_message: str | None = None) -> dict[str, str]:
    return {
        'status': 'success' if success else 'error',
        'message': success_message if success else (error_message or success_message)
    }
