"""Models for Headroom (token compression) configuration and savings."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class HeadroomStrategy(StrEnum):
    """Compression strategies supported by Headroom."""

    LOSSLESS = "lossless"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class HeadroomConfig(BaseModel):
    """Headroom settings stored on an assistant.

    Takes effect on LangGraphAgent runs only.
    """

    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    compress_user_messages: bool = True
    compress_tool_outputs: bool = True
    strategy: HeadroomStrategy = HeadroomStrategy.BALANCED


class HeadroomOverride(BaseModel):
    """Partial Headroom settings, for example on a workflow."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool | None = None
    compress_user_messages: bool | None = None
    compress_tool_outputs: bool | None = None
    strategy: HeadroomStrategy | None = None


class HeadroomSavings(BaseModel):
    """Token savings reported for a message or an execution."""

    model_config = ConfigDict(extra="ignore")

    tokens_original: int
    tokens_compacted: int
    tokens_saved: int
    # Open strings, not HeadroomStrategy, so values the backend adds later
    # (e.g. mode="mixed") still parse.
    mode: str
    strategy: str | None = None
    calls: int = 1
