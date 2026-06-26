from __future__ import annotations

from datetime import datetime
from typing import Any


def normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def format_datetime(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:  # noqa: BLE001
            return str(value)
    return str(value)


def paginate(items: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    total = len(items)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    return {
        "list": items[start:end],
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }
