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


class MarketplaceCleanupBucket(str, Enum):
    """Bucket filter of the Cleanup list; ALL lists every bucket, VERIFIED included."""

    ALL = "ALL"
    VERIFIED = "VERIFIED"
    COMMUNITY = "COMMUNITY"
    DELETE = "DELETE"


class MarketplaceCleanupOrderBy(str, Enum):
    """Sort order of the Cleanup list."""

    SCORE_DESC = "score_desc"
    USERS_DESC = "users_desc"
    USERS_ASC = "users_asc"
    LIKES_DESC = "likes_desc"
    LIKES_ASC = "likes_asc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"


class MarketplaceCleanupReason(str, Enum):
    """Why an assistant sits in the Cleanup list."""

    DUPLICATE = "duplicate"
    PURPOSE_DUPLICATE = "purpose_duplicate"
    SEMANTIC_CLONE = "semantic_clone"
    INVALID = "invalid"
    DEAD = "dead"


class MarketplaceUsageTier(str, Enum):
    """Usage tier of an assistant in the audit."""

    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"
    DEAD = "DEAD"


class MarketplaceVerdictKind(str, Enum):
    """Triage verdict of the audit for one assistant."""

    KEEP = "KEEP"
    REVIEW = "REVIEW"
    CANDIDATE_FOR_CLEANUP = "CANDIDATE_FOR_CLEANUP"


class MarketplaceGateRule(str, Enum):
    """Identifier of a deterministic quality check."""

    NAME_LENGTH = "name_length"
    NAME_NOT_BANNED = "name_not_banned"
    DESCRIPTION_LENGTH = "description_length"
    DESCRIPTION_NOT_EQUAL_NAME = "description_not_equal_name"
    SYSTEM_PROMPT_LENGTH = "system_prompt_length"
    AT_LEAST_ONE_CATEGORY = "at_least_one_category"
    SUBSTANCE = "substance"
    NO_INLINE_CREDENTIALS = "no_inline_credentials"
    CREDENTIAL_SCAN_TIMEOUT = "credential_scan_timeout"


class MarketplaceAuditRunStatus(str, Enum):
    """Lifecycle of one audit run; PENDING and RUNNING are the active states."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


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


class MarketplaceSimilarPair(BaseModel):
    """The closest other assistant the audit found for a Cleanup row."""

    model_config = ConfigDict(extra="allow")

    a_id: str
    b_id: str
    b_name: str | None = None
    b_slug: str | None = None
    b_project: str | None = None
    signals: dict[str, float] = Field(default_factory=dict)
    combined: float
    severity: str | None = None
    reason: str | None = None
    b_verdict_kind: str | None = None


class MarketplaceCleanupRow(BaseModel):
    """A row of the Cleanup list, as the table renders it.

    ``creator`` is the latest submitter's display name, else the author's display
    name, else ``None``. Unknown keys are kept, and ``model_fields_set`` lists
    exactly the keys the server sent.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    name: str | None = None
    creator: str | None = None
    categories: list[str] = Field(default_factory=list)
    unique_users_count: int | None = None
    unique_likes_count: int | None = None
    usage_tier: MarketplaceUsageTier | str | None = Field(
        None, union_mode="left_to_right"
    )
    bucket: MarketplaceCleanupBucket | str | None = Field(
        None, union_mode="left_to_right"
    )
    bucket_reason: str | None = None
    verdict_kind: MarketplaceVerdictKind | str | None = Field(
        None, union_mode="left_to_right"
    )
    cleanup_reason: MarketplaceCleanupReason | str | None = Field(
        None, union_mode="left_to_right"
    )
    canonical_id: str | None = None
    canonical_name: str | None = None
    canonical_users: int | None = None
    critical_count: int = 0
    optional_count: int = 0
    detail: str | None = None
    top_similar: MarketplaceSimilarPair | None = None


class MarketplaceCleanupResponse(BaseModel):
    """One page of the Cleanup list; ``total`` counts the whole filtered set."""

    model_config = ConfigDict(extra="allow")

    total: int
    page: int
    page_size: int
    items: list[MarketplaceCleanupRow] = Field(default_factory=list)


class MarketplaceAuditStatus(BaseModel):
    """State of the current or most recent audit run of the marketplace."""

    model_config = ConfigDict(extra="ignore")

    is_running: bool
    run_id: str | None = None
    started_at: float | None = Field(None, description="POSIX timestamp of the start")
    finished_at: float | None = Field(None, description="POSIX timestamp of the end")
    error: str | None = None
    status: MarketplaceAuditRunStatus | str | None = Field(
        None,
        union_mode="left_to_right",
        description="Status of the run; a value this SDK does not know stays a string",
    )
    similarity_backend: str | None = None
    es_doc_count: int | None = None
    degraded: bool = False
    degraded_reason: str | None = None


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
