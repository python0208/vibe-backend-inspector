from copy import deepcopy
from typing import Any


SECRET_KEYS = {"password", "token", "secret", "access_token", "refresh_token"}


def mask_secrets(value: dict[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}

    masked = deepcopy(value)
    for key, item in list(masked.items()):
        if isinstance(item, dict):
            masked[key] = mask_secrets(item)
            continue
        if key.lower() in SECRET_KEYS and item:
            masked[key] = "********"
    return masked
