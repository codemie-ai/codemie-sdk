"""Helpers for building request payloads."""

from __future__ import annotations

from typing import Any


def without_none(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop unset fields so the platform applies its defaults."""
    return {key: value for key, value in payload.items() if value is not None}
