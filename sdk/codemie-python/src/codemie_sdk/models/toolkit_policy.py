"""Models for the toolkit-management policy."""

from pydantic import BaseModel, ConfigDict


class ApprovedToolkit(BaseModel):
    """A toolkit approved by the policy, optionally limited to specific tools."""

    model_config = ConfigDict(extra="ignore")

    toolkit: str
    tools: list[str] | None = None


class ToolkitPolicy(BaseModel):
    """Effective toolkit-management policy state.

    ``flag_enabled`` is False when governance is switched off platform-wide;
    ``in_effect`` is True only when a non-empty approved list restricts toolkits.
    """

    model_config = ConfigDict(extra="ignore")

    flag_enabled: bool
    in_effect: bool
    approved_toolkits: list[ApprovedToolkit] | None = None