# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Marketplace management (assistant review queue) models for the CodeMie SDK."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketplaceStatusFilter(str, Enum):
    """Status filter of the marketplace assistants listing."""

    ALL = "ALL"
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class MarketplaceGateResult(str, Enum):
    """Filter of the pending queue by the result of the live gate checks."""

    ALL_CLEAR = "all_clear"
    HAS_CRITICAL = "has_critical"
    HAS_OPTIONAL_ONLY = "has_optional_only"


class MarketplacePendingOrderBy(str, Enum):
    """Sort order of the pending queue."""

    SUBMITTED_ASC = "submitted_asc"
    SUBMITTED_DESC = "submitted_desc"
    NAME_ASC = "name_asc"


class MarketplaceGateFinding(BaseModel):
    """One deterministic gate finding of an assistant."""

    model_config = ConfigDict(extra="ignore")

    rule: str = Field(description="Identifier of the gate rule")
    severity: str = Field(description='"CRITICAL" or "OPTIONAL"')
    message: str = Field(description="Human-readable explanation")


class MarketplacePendingRow(BaseModel):
    """Summary of an assistant waiting in the review queue."""

    model_config = ConfigDict(extra="ignore")

    assistant_id: str
    name: str | None = None
    project: str | None = None
    marketplace_status: str | None = None
    submitted_at: float | None = Field(
        None, description="POSIX timestamp of the submission"
    )
    submitted_by: str | None = None
    gate_findings: list[MarketplaceGateFinding] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    gate_recompute_failed: bool = Field(
        False, description="The gate checks could not be evaluated for this row"
    )


class MarketplacePendingResponse(BaseModel):
    """One page of the review queue."""

    model_config = ConfigDict(extra="ignore")

    total: int
    page: int
    page_size: int
    items: list[MarketplacePendingRow] = Field(default_factory=list)


class MarketplaceAssistantRow(MarketplacePendingRow):
    """A row of the marketplace assistants listing, with the review outcome."""

    is_verified: bool = False
    marketplace_decision_reason: str | None = None


class MarketplaceAssistantsResponse(BaseModel):
    """One page of the marketplace assistants listing."""

    model_config = ConfigDict(extra="ignore")

    total: int
    page: int
    page_size: int
    items: list[MarketplaceAssistantRow] = Field(default_factory=list)


class MarketplacePendingStats(BaseModel):
    """Size and waiting times of the review queue."""

    model_config = ConfigDict(extra="ignore")

    count: int = 0
    waiting_over_7d: int = 0
    avg_wait_days: float = 0.0


class MarketplaceOverview(BaseModel):
    """Marketplace health figures; only the review queue block is modelled in detail."""

    model_config = ConfigDict(extra="allow")

    total: int | None = None
    marketplace_assistants_total: int | None = None
    pending: MarketplacePendingStats = Field(default_factory=MarketplacePendingStats)


class MarketplaceReviewDetail(BaseModel):
    """What a reviewer sees about one assistant, including the live gate findings."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str
    description: str = ""
    categories: list[str] = Field(default_factory=list)
    project: str | None = None
    submitted_by: str | None = None
    marketplace_submitted_at: datetime | None = None
    marketplace_status: str | None = None
    marketplace_version: int = Field(
        0, description="Compare-and-set token to pass as expected_version"
    )
    is_global: bool | None = None
    is_verified: bool = False
    marketplace_decided_at: datetime | None = None
    marketplace_decided_by: str | None = None
    marketplace_decision_reason: str | None = None
    system_prompt_length: int = 0
    gate_findings: list[MarketplaceGateFinding] = Field(default_factory=list)
    critical_count: int = 0
    optional_count: int = 0
    override_notice: str | None = None
    overridden_by: str | None = None
    bypassed_gate_findings: list[MarketplaceGateFinding] | None = None
    bypassed_gate_findings_unavailable: bool = False


class MarketplaceIndexingOutcome(BaseModel):
    """What happened to the search-index projection of a decision."""

    model_config = ConfigDict(extra="ignore")

    action: str = Field(description='"index" or "remove"')
    state: str = Field(description='"OK" or "FAILED"')
    attempts: int = 0
    error: str | None = None


class MarketplaceReviewActionResponse(BaseModel):
    """Outcome of approve, reject or withdraw."""

    model_config = ConfigDict(extra="ignore")

    ok: bool
    entity_kind: str
    entity_id: str
    status: str = Field(description="Marketplace status after the decision")
    indexing: MarketplaceIndexingOutcome | None = None


class MarketplaceForcePublishResponse(MarketplaceReviewActionResponse):
    """Force-publish also echoes the notice and the findings it waived."""

    override_notice: str
    bypassed_gate_findings: list[MarketplaceGateFinding] = Field(default_factory=list)
    bypassed_gate_findings_unavailable: bool = False


class MarketplaceDecisionRequest(BaseModel):
    """Body of a review decision; only the fields that are set are sent."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
    override_notice: str | None = None
    expected_version: int | None = Field(
        None,
        ge=0,
        description="Apply only if the assistant is still at this marketplace_version",
    )

    def to_body(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
