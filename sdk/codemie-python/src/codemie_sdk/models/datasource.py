import logging
import re
import warnings
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal, Tuple

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .common import TokensUsage, User

logger = logging.getLogger(__name__)


class CodeDataSourceType(str, Enum):
    CODE = "code"
    SUMMARY = "summary"
    CHUNK_SUMMARY = "chunk-summary"


class DataSourceType(str, Enum):
    CODE = "code"
    CONFLUENCE = "knowledge_base_confluence"
    JIRA = "knowledge_base_jira"
    FILE = "knowledge_base_file"
    XRAY = "knowledge_base_xray"
    GOOGLE = "llm_routing_google"
    GIT_FAQ = "knowledge_base_git_faq"
    PROVIDER = "provider"
    SUMMARY = "summary"
    CHUNK_SUMMARY = "chunk-summary"
    JSON = "knowledge_base_json"
    BEDROCK = "knowledge_base_bedrock"
    PLATFORM = "platform_marketplace_assistant"
    AZURE_DEVOPS_WIKI = "knowledge_base_azure_devops_wiki"
    AZURE_DEVOPS_WORK_ITEM = "knowledge_base_azure_devops_work_item"
    SHAREPOINT = "knowledge_base_sharepoint"
    XWIKI = "knowledge_base_xwiki"
    # Request routing only: the backend stores SVN datasources with the index_type
    # the caller picked (code / summary / chunk-summary) and vcs_type="svn", so
    # filtering list() by SVN returns nothing.
    SVN = "svn"


class DataSourceStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    FETCHING = "fetching"
    IN_PROGRESS = "in_progress"


class DataSourceProcessingInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_documents_count: int | None = Field(None, alias="total_documents")
    skipped_documents_count: int | None = Field(None, alias="skipped_documents")
    total_size_kb: float | None = None
    average_file_size_bytes: float | None = None
    unique_extensions: list[str] | None = None
    filtered_documents: int | list | None = None
    processed_documents_count: int | None = Field(None, alias="documents_count_key")


class ElasticsearchStatsResponse(BaseModel):
    """Response model for Elasticsearch index statistics."""

    model_config = ConfigDict(extra="ignore")

    index_name: str = Field(..., description="Name of the index in Elasticsearch")
    size_in_bytes: int = Field(..., ge=0, description="Size of the index in bytes")


# Base request models
class Confluence(BaseModel):
    """Model for Confluence-specific response fields"""

    cql: str | None = None
    include_restricted_content: bool | None = None
    include_archived_content: bool | None = None
    include_attachments: bool | None = None
    include_comments: bool | None = None
    keep_markdown_format: bool | None = None
    keep_newlines: bool | None = None
    max_pages: int | None = None
    pages_per_request: int | None = None

    model_config = ConfigDict(extra="ignore")


class Jira(BaseModel):
    """Model for Jira-specific response fields"""

    jql: str | None = None
    custom_fields: list[str] | None = None

    model_config = ConfigDict(extra="ignore")


class Google(BaseModel):
    """Model for Google-specific response fields"""

    google_doc: str = Field(None, alias="googleDoc")

    model_config = ConfigDict(extra="ignore")


class File(BaseModel):
    """Model for File-specific response fields"""

    files: list[Tuple[str, bytes, str]] | None = None  # (filename, content, mime_type)

    model_config = ConfigDict(extra="ignore")


class AzureDevOpsWiki(BaseModel):
    """Model for Azure DevOps Wiki-specific response fields"""

    wiki_query: str | None = None
    organization: str | None = None
    project: str | None = None
    wiki_name: str | None = None

    model_config = ConfigDict(extra="ignore")


class AzureDevOpsWorkItem(BaseModel):
    """Model for Azure DevOps Work Item-specific response fields"""

    wiql_query: str | None = None
    organization: str | None = None
    project: str | None = None

    model_config = ConfigDict(extra="ignore")


class XWiki(BaseModel):
    """Model for xWiki-specific response fields"""

    space: str | None = None
    wiki: str | None = None

    model_config = ConfigDict(extra="ignore")


class Svn(BaseModel):
    """Model for SVN repository datasource fields.

    Note: the backend PUT resets omitted prompt, files_filter, project_space_visible
    and docs_generation to defaults, so send them on every update. The update
    request uses the camelCase names the backend update endpoint reads.
    """

    link: str = Field(..., min_length=1, max_length=1000)
    branch: str = Field("trunk", min_length=1, max_length=1000)
    files_filter: str | None = None
    embeddings_model: str | None = None
    prompt: str | None = None
    docs_generation: bool | None = None

    model_config = ConfigDict(extra="ignore")


class SharePoint(BaseModel):
    """Model for SharePoint-specific request fields."""

    site_url: str = Field(..., pattern=r"^https://\S+$", max_length=1000)
    include_pages: bool | None = None
    include_documents: bool | None = None
    include_lists: bool | None = None
    max_file_size_mb: int | None = Field(None, ge=1, le=500)
    files_filter: str | None = None
    auth_type: Literal["integration", "oauth_codemie", "oauth_custom"] | None = None
    oauth_client_id: str | None = None
    oauth_tenant_id: str | None = None
    access_token: str | None = Field(None, repr=False)
    embedding_model: str | None = None

    model_config = ConfigDict(extra="ignore")


class Xray(BaseModel):
    """Model for Xray-specific fields"""

    jql: str = Field(..., min_length=1)
    embedding_model: str | None = None

    model_config = ConfigDict(extra="ignore")


class SvnInfo(BaseModel):
    """Typed read of the SVN settings stored on a datasource (vcs_type=svn)."""

    link: str | None = None
    branch: str | None = None
    files_filter: str | None = None
    embeddings_model: str | None = None
    prompt: str | None = None
    docs_generation: bool | None = None

    model_config = ConfigDict(extra="ignore")


class SharePointInfo(BaseModel):
    """Typed read of the nested SharePoint config (credentials are not exposed)."""

    site_url: str | None = None
    include_pages: bool | None = None
    include_documents: bool | None = None
    include_lists: bool | None = None
    max_file_size_mb: int | None = None
    files_filter: str | None = None
    auth_type: str | None = None
    oauth_client_id: str | None = None
    oauth_tenant_id: str | None = None

    model_config = ConfigDict(extra="ignore")


class XrayInfo(BaseModel):
    """Typed read of the nested Xray config."""

    jql: str | None = None

    model_config = ConfigDict(extra="ignore")


class ProviderFields(BaseModel):
    """Typed read of provider datasource settings.

    Sensitive params are encrypted at rest, so a read can return ciphertext rather
    than the secret. On update, send ``**********`` for a secret to keep the stored
    value.
    """

    provider_id: str | None = None
    toolkit_id: str | None = None
    base_params: dict[str, Any] = Field(default_factory=dict)
    create_params: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    @field_validator("base_params", "create_params", mode="before")
    def null_params_as_empty(cls, value):
        return {} if value is None else value


class Code(BaseModel):
    """Model for code repository datasource creation"""

    model_config = ConfigDict(populate_by_name=True)

    link: str | None = Field(..., min_length=1, max_length=1000)
    branch: str | None = Field(..., min_length=1, max_length=1000)
    index_type: CodeDataSourceType | None = Field(None, alias="indexType")
    files_filter: str | None = Field(default="", alias="filesFilter")
    embeddings_model: str | None = Field(None, alias="embeddingsModel")
    summarization_model: str | None = Field(None, alias="summarizationModel")
    prompt: str | None = None
    docs_generation: bool = Field(False, alias="docsGeneration")


class GitFaq(BaseModel):
    """Model for the Git FAQ (knowledge_base_git_faq) datasource creation"""

    link: str | None = Field(..., min_length=1, max_length=1000)
    branch: str | None = Field(..., min_length=1, max_length=1000)
    files_filter: str | None = Field(None)
    embedding_model: str | None = Field(None)


class CodeInfo(BaseModel):
    """Typed read of a code datasource's settings; every field is optional."""

    link: str | None = None
    branch: str | None = None
    index_type: CodeDataSourceType | None = None
    files_filter: str | None = None
    embeddings_model: str | None = None
    summarization_model: str | None = None
    prompt: str | None = None
    docs_generation: bool | None = None

    model_config = ConfigDict(extra="ignore")


class GitFaqInfo(BaseModel):
    """Typed read of a Git FAQ datasource's settings; every field is optional."""

    link: str | None = None
    branch: str | None = None
    files_filter: str | None = None
    embedding_model: str | None = None

    model_config = ConfigDict(extra="ignore")


class BaseDataSourceRequest(BaseModel):
    """Base model for all datasource creation requests"""

    name: str = Field(
        ...,
        description="Name must contain only lowercase letters and underscores.",
        max_length=50,
    )
    project_name: str
    description: str = Field(..., max_length=100)
    shared_with_project: bool = Field(False, alias="project_space_visible")
    setting_id: str | None = Field(None)
    type: DataSourceType
    cron_expression: str | None = Field(None)
    timezone: str | None = Field(None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @classmethod
    def required_fields(cls) -> list[str]:
        return []

    @field_validator("name")
    def validate_name_field(cls, value):
        if not re.fullmatch(r"^[a-z][a-z_-]*$", value):
            raise ValueError(
                "Name must contain only lowercase letters and underscores, and cannot begin with '_' or '-'."
            )
        return value

    @model_validator(mode="before")
    def pre_init_validator(cls, values):
        # Ensure that at least one of the fields is not None
        if cls.required_fields() and not any(
            values.get(field) for field in cls.required_fields()
        ):
            raise ValueError(
                f"At least one of the following fields must be set: {', '.join(cls.required_fields())}"
            )
        return values


class CodeDataSourceRequest(BaseDataSourceRequest, Code):
    # Override to comply with keys in json
    project_space_visible: bool = Field(False, alias="projectSpaceVisible")
    setting_id: str | None = Field(None, alias="settingId")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.CODE, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["link", "embeddings_model", "branch", "index_type"]


class GitFaqDataSourceRequest(BaseDataSourceRequest, GitFaq):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.GIT_FAQ, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["link", "branch"]


class JiraDataSourceRequest(BaseDataSourceRequest, Jira):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.JIRA, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["jql"]


class ConfluenceDataSourceRequest(BaseDataSourceRequest, Confluence):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.CONFLUENCE, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["cql"]


class GoogleDataSourceRequest(BaseDataSourceRequest, Google):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.GOOGLE, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["google_doc"]


class FileDataSourceRequest(BaseDataSourceRequest):
    """Model for File datasource creation requests"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.FILE, **data)


class AzureDevOpsWikiDataSourceRequest(BaseDataSourceRequest, AzureDevOpsWiki):
    """Model for Azure DevOps Wiki datasource creation requests"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.AZURE_DEVOPS_WIKI, **data)


class AzureDevOpsWorkItemDataSourceRequest(BaseDataSourceRequest, AzureDevOpsWorkItem):
    """Model for Azure DevOps Work Item datasource creation requests"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.AZURE_DEVOPS_WORK_ITEM, **data)


class XWikiDataSourceRequest(BaseDataSourceRequest, XWiki):
    """Model for xWiki datasource creation requests"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.XWIKI, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["space"]


class SvnDataSourceRequest(BaseDataSourceRequest, Svn):
    """Model for SVN datasource creation requests"""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    index_type: CodeDataSourceType = Field(..., alias="indexType")
    # Used by the summary and chunk-summary index types; the backend falls back
    # to its default model when omitted.
    summarization_model: str | None = Field(None, alias="summarizationModel")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.SVN, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["link"]


class SharePointDataSourceRequest(BaseDataSourceRequest, SharePoint):
    """Model for SharePoint datasource creation requests"""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @model_validator(mode="after")
    def validate_oauth_access_token(self):
        if (
            self.auth_type in ("oauth_codemie", "oauth_custom")
            and not self.access_token
        ):
            raise ValueError(
                "access_token is required when auth_type is 'oauth_codemie' or 'oauth_custom'"
            )
        return self

    def __init__(self, **data):
        super().__init__(type=DataSourceType.SHAREPOINT, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["site_url"]


class XrayDataSourceRequest(BaseDataSourceRequest, Xray):
    """Model for Xray datasource creation requests"""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.XRAY, **data)

    @classmethod
    def required_fields(cls) -> list[str]:
        return ["jql"]


class BaseUpdateDataSourceRequest(BaseDataSourceRequest):
    """Mixin update-specific reindex fields"""

    full_reindex: bool | None = Field(None)
    skip_reindex: bool | None = Field(None)
    resume_indexing: bool | None = Field(None)
    incremental_reindex: bool | None = Field(None)

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @model_validator(mode="after")
    def validate_reindex_options(self) -> "BaseUpdateDataSourceRequest":
        ds_type = self.type

        if ds_type == DataSourceType.CONFLUENCE:
            if self.incremental_reindex:
                raise ValueError(
                    "Confluence data sources only support full_reindex and resume_indexing"
                )

        elif ds_type == DataSourceType.JIRA:
            if self.resume_indexing:
                raise ValueError(
                    "Jira data sources only support full_reindex and incremental_reindex"
                )

        elif ds_type == DataSourceType.CODE:
            if self.incremental_reindex:
                raise ValueError("Code data sources do not support incremental_reindex")

        elif ds_type == DataSourceType.GOOGLE:
            if self.resume_indexing or self.incremental_reindex:
                raise ValueError("Google data sources only support full_reindex")

        return self


class UpdateGitFaqDataSourceRequest(BaseUpdateDataSourceRequest):
    """Model for Git FAQ datasource updates; source fields require full_reindex=True"""

    link: str | None = Field(None)
    branch: str | None = Field(None)
    files_filter: str | None = Field(None)
    setting_id: str | None = Field(None)

    def __init__(self, **data):
        super().__init__(type=DataSourceType.GIT_FAQ, **data)


class UpdateCodeDataSourceRequest(BaseUpdateDataSourceRequest, Code):
    """Model for code repository datasource updates"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.CODE, **data)


class UpdateConfluenceDataSourceRequest(BaseUpdateDataSourceRequest, Confluence):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.CONFLUENCE, **data)


class UpdateJiraDataSourceRequest(BaseUpdateDataSourceRequest, Jira):
    def __init__(self, **data):
        super().__init__(type=DataSourceType.JIRA, **data)


class UpdateGoogleDataSourceRequest(BaseUpdateDataSourceRequest):
    """Model for Google docs datasource updates"""

    google_doc: str | None = Field(None, alias="googleDoc")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.GOOGLE, **data)


class UpdateFileDataSourceRequest(BaseUpdateDataSourceRequest):
    """Model for File datasource updates"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.FILE, **data)


class UpdateAzureDevOpsWikiDataSourceRequest(
    BaseUpdateDataSourceRequest, AzureDevOpsWiki
):
    """Model for Azure DevOps Wiki datasource updates"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.AZURE_DEVOPS_WIKI, **data)


class UpdateAzureDevOpsWorkItemDataSourceRequest(
    BaseUpdateDataSourceRequest, AzureDevOpsWorkItem
):
    """Model for Azure DevOps Work Item datasource updates"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.AZURE_DEVOPS_WORK_ITEM, **data)


class UpdateXWikiDataSourceRequest(BaseUpdateDataSourceRequest, XWiki):
    """Model for xWiki datasource updates"""

    def __init__(self, **data):
        super().__init__(type=DataSourceType.XWIKI, **data)


class UpdateSvnDataSourceRequest(BaseUpdateDataSourceRequest, Svn):
    """Model for SVN datasource updates (camelCase keys, as the backend reads them)"""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # The backend writes these four on every update, sent or not (a missing
    # visibility flag becomes True, a missing prompt / filter / docs flag is
    # wiped), so the caller states each one. ``None`` is allowed for the
    # nullable three and means "clear it"; it is not sent.
    shared_with_project: bool = Field(
        ...,
        validation_alias=AliasChoices(
            "projectSpaceVisible", "project_space_visible", "shared_with_project"
        ),
        serialization_alias="projectSpaceVisible",
    )
    prompt: str | None = Field(...)
    files_filter: str | None = Field(..., alias="filesFilter")
    docs_generation: bool | None = Field(..., alias="docsGeneration")
    # Optional on update: the backend overwrites the stored link / branch when sent.
    link: str | None = Field(None, min_length=1, max_length=1000)
    branch: str | None = Field(None, min_length=1, max_length=1000)
    embeddings_model: str | None = Field(None, alias="embeddingsModel")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.SVN, **data)


class UpdateSharePointDataSourceRequest(BaseUpdateDataSourceRequest, SharePoint):
    """Model for SharePoint datasource updates (site_url is optional: omit to keep it)"""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    site_url: str | None = Field(None, pattern=r"^https://\S+$", max_length=1000)
    # None keeps the stored value (the backend update treats a missing flag so).
    shared_with_project: bool | None = Field(None, alias="project_space_visible")

    @model_validator(mode="after")
    def validate_oauth_reindex_token(self):
        # The backend saves the update first and only then refuses a reindex of an
        # OAuth datasource without a token (422), leaving a partial apply. Only an
        # explicit auth_type can be checked here; a stored OAuth type with
        # auth_type omitted still needs the token on every full_reindex.
        if (
            self.full_reindex
            and self.auth_type in ("oauth_codemie", "oauth_custom")
            and not self.access_token
        ):
            raise ValueError(
                "access_token is required for full_reindex when auth_type is "
                "'oauth_codemie' or 'oauth_custom'"
            )
        return self

    def __init__(self, **data):
        super().__init__(type=DataSourceType.SHAREPOINT, **data)


class UpdateXrayDataSourceRequest(BaseUpdateDataSourceRequest):
    """Model for Xray datasource updates.

    Does not extend ``Xray``: the backend update ignores ``embedding_model`` (it is
    create-only), so it is rejected here instead of being sent and dropped.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    jql: str = Field(..., min_length=1)
    # None keeps the stored value (the backend update treats a missing flag so).
    shared_with_project: bool | None = Field(None, alias="project_space_visible")

    def __init__(self, **data):
        super().__init__(type=DataSourceType.XRAY, **data)


class CodeAnalysisDataSourceRequest(BaseModel):
    """Model for provider-based datasource creation requests.

    Deprecated: targets the standalone 'CodeAnalysisServiceProvider', which
    the combined AICE provider (CodeExplorationToolkit) has superseded for
    datasource creation. Kept for now since we have not confirmed that
    provider type is fully retired on every deployment — use
    CodeExplorationDataSourceRequest for new code.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(..., description="Datasource name")
    description: str = Field("", description="Datasource description")
    project_name: str = Field(..., description="Project name")
    project_space_visible: bool = Field(
        False, description="Make the datasource visible to the whole project"
    )
    branch: str | None = Field(None, description="Git branch")
    api_url: str = Field(..., description="Repository URL")
    access_token: str = Field(..., description="Access token for repository")
    analyzer: str | None = Field(
        None, description="Code analyzer type (e.g., Java, Python)"
    )
    datasource_root: str = Field("/", description="Root directory to analyze")

    def __init__(self, **data):
        warnings.warn(
            "CodeAnalysisDataSourceRequest targets the standalone "
            "'CodeAnalysisServiceProvider', superseded by the combined AICE "
            "provider. Use CodeExplorationDataSourceRequest instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class CodeExplorationDataSourceRequest(BaseModel):
    """Model for CodeExplorationToolkit datasource creation requests"""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(..., description="Datasource name")
    description: str = Field("", description="Datasource description")
    project_name: str = Field(..., description="Project name")
    project_space_visible: bool = Field(
        False, description="Make the datasource visible to the whole project"
    )
    code_analysis_datasource_ids: list[str] | None = Field(
        None,
        alias="code_analysis_datasource_ids",
        description="List of CodeAnalysisToolkit datasource IDs. Optional: the "
        "combined AICE provider creates a CodeExplorationToolkit datasource from "
        "name/description alone, with no separate CodeAnalysisToolkit datasources.",
    )


class _ProviderRequestBase(BaseModel):
    """Shared fields and body of the provider create and update requests."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # The backend writes name, project_name, description and
    # project_space_visible from the body on every update without a None check,
    # so all four are required (a missing one is stored as NULL and the save fails).
    name: str = Field(..., min_length=1)
    project_name: str = Field(..., min_length=1)
    description: str
    project_space_visible: bool
    settings: dict[str, Any] = Field(default_factory=dict)

    def to_body(self) -> dict[str, Any]:
        """Body with name, project_name, description and project_space_visible
        merged with settings."""
        return {
            **self.settings,
            "name": self.name,
            "project_name": self.project_name,
            "description": self.description,
            "project_space_visible": self.project_space_visible,
        }


class UpdateProviderDataSourceRequest(_ProviderRequestBase):
    """Typed update request for provider datasources."""


class ProviderDataSourceRequest(_ProviderRequestBase):
    """Typed create request for provider datasources.

    provider_name and toolkit_id are sent as query params, not in the body.
    """

    provider_name: str
    toolkit_id: str


class DataSource(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    def __getitem__(self, key):
        return getattr(self, key)

    id: str
    project_name: str
    name: str = Field(None, alias="repo_name")
    description: str | None = Field(None)
    type: DataSourceType = Field(None, alias="index_type")
    embeddings_model: str | None = Field(None)
    status: DataSourceStatus
    setting_id: str | None = Field(None)
    created_date: datetime = Field(None, alias="date")
    created_by: User
    shared_with_project: bool = Field(None, alias="project_space_visible")
    cron_expression: str | None = None
    timezone: str | None = None
    update_date: datetime
    error_message: str | None = Field(None, alias="text")
    user_abilities: list[str]
    processing_info: DataSourceProcessingInfo | None = Field(None)
    processed_documents: list[str] | None = Field(None, alias="processed_files")
    tokens_usage: TokensUsage | None = Field(None)
    # Code specific fields
    code: CodeInfo | None = None
    git_faq: GitFaqInfo | None = None
    # Jira specific fields
    jira: Jira | None = None
    # Confluence specific fields
    confluence: Confluence | None = None
    # Google doc specific fields
    google_doc_link: str | None = None
    # Azure DevOps Wiki specific fields
    azure_devops_wiki: AzureDevOpsWiki | None = None
    # Azure DevOps Work Item specific fields
    azure_devops_work_item: AzureDevOpsWorkItem | None = None
    # xWiki specific fields
    xwiki: XWiki | None = None
    # SVN, SharePoint, Xray and provider specific fields
    svn: SvnInfo | None = None
    sharepoint: SharePointInfo | None = None
    xray: XrayInfo | None = None
    provider: ProviderFields | None = None

    @field_validator(
        "code", "git_faq", "svn", "sharepoint", "xray", "provider", mode="wrap"
    )
    def tolerate_unreadable_sub_object(cls, value, handler, info):
        # One stored record with an unexpected shape must not break the whole read.
        try:
            return handler(value)
        except ValidationError as error:
            logger.warning(
                "Ignoring unreadable %s settings of datasource %s: %s",
                info.field_name,
                info.data.get("id"),
                error.errors(include_url=False, include_input=False),
            )
            return None

    @model_validator(mode="before")
    def before_init(cls, values):
        if values.get("error"):
            values["status"] = DataSourceStatus.FAILED
        elif values.get("completed"):
            values["status"] = DataSourceStatus.COMPLETED
        elif values.get("is_fetching"):
            values["status"] = DataSourceStatus.FETCHING
        else:
            values["status"] = DataSourceStatus.IN_PROGRESS

        builder = _INDEX_TYPE_BUILDERS.get(values.get("index_type"))
        if builder:
            builder(values)
        if values.get("provider_fields"):
            values["provider"] = values["provider_fields"]
        return values


def _picked(values: dict, model: type[BaseModel]) -> dict:
    return {name: values[name] for name in model.model_fields if name in values}


def _build_processing_info(values: dict) -> None:
    complete_state = values.get("complete_state", 0)
    if complete_state is not None:
        values["processing_info"] = {"documents_count_key": complete_state}


def _sub_object_builder(
    key: str,
    source: Callable[[dict], dict],
) -> Callable[[dict], None]:
    def build(values: dict) -> None:
        values[key] = source(values)

    return build


def _present(values: dict, names: tuple[str, ...]) -> dict:
    return {name: values[name] for name in names if values.get(name) is not None}


def _git_faq_source(values: dict) -> dict:
    data = _present(values, ("link", "branch", "files_filter"))
    if values.get("embeddings_model") is not None:
        data["embedding_model"] = values["embeddings_model"]
    return data


_CODE_FIELDS = (
    "link",
    "branch",
    "index_type",
    "files_filter",
    "embeddings_model",
    "summarization_model",
    "prompt",
    "docs_generation",
)


def _code_source(values: dict) -> dict:
    return _present(values, _CODE_FIELDS)


_build_git_faq = _sub_object_builder("git_faq", _git_faq_source)
_build_code_info = _sub_object_builder("code", _code_source)


def _build_code(values: dict) -> None:
    _build_code_info(values)
    # SVN datasources are stored with a code index_type and vcs_type="svn".
    if values.get("vcs_type") == "svn":
        values["svn"] = _picked(values, SvnInfo)


# index_type -> builder that derives typed sub-objects from the flat payload.
_INDEX_TYPE_BUILDERS: dict[str, Callable[[dict], None]] = {
    **{
        index_type: _build_processing_info
        for index_type in (
            DataSourceType.CONFLUENCE,
            DataSourceType.JIRA,
            DataSourceType.GOOGLE,
            DataSourceType.AZURE_DEVOPS_WIKI,
            DataSourceType.AZURE_DEVOPS_WORK_ITEM,
            DataSourceType.XWIKI,
        )
    },
    DataSourceType.GIT_FAQ: _build_git_faq,
    DataSourceType.CODE: _build_code,
    DataSourceType.SUMMARY: _build_code,
    DataSourceType.CHUNK_SUMMARY: _build_code,
}
