"""Small value helpers."""


def first_not_none(preferred, fallback):
    """Return ``preferred`` unless it is None, otherwise ``fallback``."""
    return fallback if preferred is None else preferred
