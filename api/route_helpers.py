from collections.abc import Iterable
from typing import Any

from utils.api_helpers import status_message_response, success_response


def serialize_items(items: Iterable[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in items]


def list_response(items: Iterable[Any], *, clean_nan: bool = True) -> dict[str, Any]:
    return success_response(data=serialize_items(items), clean_nan=clean_nan)


def bool_status_response(success: bool, success_message: str, error_message: str) -> dict[str, str]:
    return status_message_response(success, success_message, error_message)
