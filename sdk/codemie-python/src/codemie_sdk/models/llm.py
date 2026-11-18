"""Models for LLM service."""

from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


class LLMProvider(str, Enum):
    """LLM provider options."""

    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    GOOGLE_VERTEXAI = "google_vertexai"
    GOOGLE_VERTEXAI_ANTHROPIC = "vertex_ai-anthropic_models"
    ANTHROPIC = "anthropic"


class ModelStatus(str, Enum):
    """Platform-managed status of an LLM model."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


def _coerce_model_status(value: Any) -> Any:
    """Return a ModelStatus for known values and keep unknown ones as they are."""
    try:
        return ModelStatus(value)
    except ValueError:
        return value


# Response-side status: a status the SDK does not know yet must not fail parsing.
ModelStatusValue = Annotated[ModelStatus | str, BeforeValidator(_coerce_model_status)]


class EffortLevel(str, Enum):
    """Reasoning effort levels, in ascending order."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"


class CostConfig(BaseModel):
    """Cost configuration for LLM model."""

    input: float
    output: float


class LLMFeatures(BaseModel):
    """Features supported by LLM model."""

    streaming: bool | None = True
    tools: bool | None = True
    temperature: bool | None = True
    parallel_tool_calls: bool | None = True
    system_prompt: bool | None = True
    max_tokens: bool | None = True
    # Effort levels the model accepts, or None when the model has no effort support.
    effort: list[EffortLevel] | None = None


class LLMModel(BaseModel):
    """LLM model configuration."""

    base_name: str
    deployment_name: str | None = None
    label: str | None = None
    multimodal: bool | None = None
    react_agent: bool | None = None
    enabled: bool
    provider: LLMProvider | None = None
    default: bool | None = None
    cost: CostConfig | None = None
    max_output_tokens: int | None = None
    features: LLMFeatures | None = Field(default_factory=lambda: LLMFeatures())
    is_premium: bool | None = None
    is_router: bool | None = None
    supports_tools: bool | None = None
    status: ModelStatusValue | None = None
