"""A2A (agent-to-agent) models; AgentCard accepts both v1.0 and legacy (v0.3) cards."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentProvider(BaseModel):
    """Provider information for an A2A agent card."""

    model_config = ConfigDict(extra="ignore")

    organization: str | None = None
    url: str | None = None


class AgentInterface(BaseModel):
    """A transport interface the agent exposes (A2A v1.0)."""

    model_config = ConfigDict(extra="ignore")

    url: str
    protocolBinding: str | None = None
    protocolVersion: str | None = None


class AgentCapabilities(BaseModel):
    """Capabilities advertised by an A2A agent card."""

    model_config = ConfigDict(extra="ignore")

    streaming: bool = False
    pushNotifications: bool = False
    extendedAgentCard: bool = False
    stateTransitionHistory: bool = False


class AgentAuthentication(BaseModel):
    """Authentication schemes advertised by a legacy (v0.3) A2A agent card."""

    model_config = ConfigDict(extra="ignore")

    schemes: list[str]
    credentials: str | None = None


class AgentSkill(BaseModel):
    """A single skill exposed by an A2A agent card."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str | None = None
    tags: list[str] | None = None
    examples: list[str] | None = None
    inputModes: list[str] | None = None
    outputModes: list[str] | None = None


class AgentCard(BaseModel):
    """A2A agent card describing an assistant for agent discovery."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: str | None = None
    supportedInterfaces: list[AgentInterface] = []
    provider: AgentProvider | None = None
    version: str
    documentationUrl: str | None = None
    capabilities: AgentCapabilities
    securitySchemes: dict[str, dict[str, Any]] | None = None
    securityRequirements: list[dict[str, Any]] | None = None
    defaultInputModes: list[str] = []
    defaultOutputModes: list[str] = []
    skills: list[AgentSkill]
    # Legacy (v0.3) fields, absent from v1.0 cards
    url: str | None = None
    authentication: AgentAuthentication | None = None

    @property
    def protocol_version(self) -> str | None:
        """Protocol version of the first advertised interface, or None for legacy cards."""
        if self.supportedInterfaces:
            return self.supportedInterfaces[0].protocolVersion
        return None
