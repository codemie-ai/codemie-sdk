"""Admin models for managing applications/projects."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .llm import ModelStatus, ModelStatusValue


class ApplicationInfo(BaseModel):
    """Single application entry returned by GET /v1/admin/applications."""

    model_config = ConfigDict(extra="ignore")

    name: str
    display_name: str | None = None


class ApplicationsListResponse(BaseModel):
    """Response model for list applications endpoint."""

    model_config = ConfigDict(extra="ignore")

    applications: list[ApplicationInfo] = Field(
        ..., description="List of application info objects"
    )


class ApplicationCreateRequest(BaseModel):
    """Request model for creating an application/project."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Application/project name")


class ApplicationCreateResponse(BaseModel):
    """Response model for create application endpoint."""

    model_config = ConfigDict(extra="ignore")

    message: str = Field(..., description="Created application name")


class LocalUserCreateRequest(BaseModel):
    """Request model for admin user creation (local auth mode only)."""

    model_config = ConfigDict(extra="ignore")

    email: str
    username: str
    password: str
    name: str | None = None
    is_admin: bool = False
    is_maintainer: bool = False


class LocalUserDetail(BaseModel):
    """Response model for created/fetched user (local auth mode)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    email: str
    username: str


class AdminUserListItem(BaseModel):
    """User item returned by the admin list-users endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: str
    email: str
    username: str


class AdminUserListPagination(BaseModel):
    """Pagination metadata from GET /v1/admin/users."""

    model_config = ConfigDict(extra="ignore")

    total: int
    page: int
    per_page: int


class AdminUserListResponse(BaseModel):
    """Paginated response from GET /v1/admin/users."""

    model_config = ConfigDict(extra="ignore")

    data: list[AdminUserListItem]
    pagination: AdminUserListPagination

    @property
    def users(self) -> list[AdminUserListItem]:
        return self.data

    @property
    def total(self) -> int:
        return self.pagination.total


class AdminModelCost(BaseModel):
    """Per-token cost of a model in the admin catalog."""

    model_config = ConfigDict(extra="ignore")

    input: float
    output: float


class AdminLLMModel(BaseModel):
    """Model entry returned by GET /v1/admin/llm/status."""

    model_config = ConfigDict(extra="ignore")

    base_name: str
    label: str
    model_type: str = Field(description="chat, embedding or audio_transcription")
    enabled: bool
    status: ModelStatusValue
    provider: str | None = None
    router_type: str | None = Field(
        default=None,
        description="Set for routers; their status is computed and cannot be changed",
    )
    is_premium: bool | None = None
    multimodal: bool | None = None
    supports_tools: bool | None = None
    supports_image_generation: bool = False
    cost: AdminModelCost | None = None
    updated_by_name: str | None = None
    updated_at: datetime | None = None


class LLMModelStatusUpdate(BaseModel):
    """Result of setting the status of one model."""

    model_config = ConfigDict(extra="ignore")

    base_name: str
    status: ModelStatusValue


class LLMModelStatusBulkItem(BaseModel):
    """One requested status change in a bulk update."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    base_name: str
    status: ModelStatus


class LLMModelStatusBulkItemResult(BaseModel):
    """Outcome of one item of a bulk status update."""

    model_config = ConfigDict(extra="ignore")

    base_name: str
    status: ModelStatusValue
    success: bool
    error: str | None = None


class LLMModelStatusBulkResult(BaseModel):
    """Summary of a bulk status update; every item is processed independently."""

    model_config = ConfigDict(extra="ignore")

    total: int
    succeeded: int
    failed: int
    results: list[LLMModelStatusBulkItemResult] = Field(default_factory=list)


class GlobalDefaultLLMModel(BaseModel):
    """Global default model as returned by /v1/admin/llm/default."""

    model_config = ConfigDict(extra="ignore")

    saved_base_name: str | None = Field(
        default=None, description="The model an administrator saved, if any"
    )
    updated_by_id: str | None = None
    updated_by_name: str | None = None
    updated_at: datetime | None = None
    effective_base_name: str | None = Field(
        default=None, description="The model the platform actually uses as default"
    )
    source: str | None = None
    temporary_fallback: bool = Field(
        default=False,
        description="True when the saved model is not usable and another one is used",
    )
