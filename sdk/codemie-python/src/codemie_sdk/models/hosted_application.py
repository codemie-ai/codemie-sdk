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

"""Hosted application models for the CodeMie SDK.

Shapes of the management API under ``/v1/hosted-applications``: applications, their
versions and uploads, sharing and the launch ticket of a viewing session.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HostedApplicationCapabilities(BaseModel):
    """What the caller may do with hosted applications on this stand."""

    model_config = ConfigDict(extra="ignore")

    create: bool = Field(description="The caller may create applications")
    view: bool = Field(description="The caller may open applications")
    disabled_reason: str | None = Field(
        default=None, description="Why the feature is unavailable, when it is"
    )
    launch_policy: dict[str, Any] | None = None
    limits: dict[str, Any] = Field(default_factory=dict)


class HostedApplicationUsage(BaseModel):
    """Storage quota of the caller, in bytes."""

    model_config = ConfigDict(extra="ignore")

    byte_limit: int
    available_bytes: int
    stored_bytes: int
    reserved_bytes: int


class HostedApplicationCreator(BaseModel):
    """The user who created an application."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    username: str | None = None
    name: str | None = None


class HostedApplicationCategory(BaseModel):
    """A category of an application: its id and its name."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class HostedApplication(BaseModel):
    """An application as the caller sees it.

    The fields after ``has_cover`` are present for managers only.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str | None = None
    artifact_kind: str | None = None
    updated_at: str | None = None
    publisher: dict[str, Any] | None = None
    project: str | None = None
    shared: bool = False
    is_global: bool = False
    categories: list[HostedApplicationCategory] = Field(
        default_factory=list,
        description="Categories of the application, in the order they were set",
    )
    created_by: HostedApplicationCreator | None = None
    user_abilities: list[str] = Field(default_factory=list)
    can_share: bool = False
    can_moderate: bool = False
    suspended: bool = False
    suspension_refuses: Any = None
    has_active_version: bool = False
    has_cover: bool = False
    selected_version_id: str | None = None
    active_version_id: str | None = None
    lifecycle_state: str | None = None
    revision: int | None = None
    etag: str | None = Field(
        default=None, description="Value to send as If-Match on the next change"
    )
    created_at: str | None = None


class HostedApplicationList(BaseModel):
    """One page of applications."""

    model_config = ConfigDict(extra="ignore")

    items: list[HostedApplication] = Field(default_factory=list)
    next_cursor: str | None = None


class HostedApplicationVersionStart(BaseModel):
    """A new version whose artifact is yet to be uploaded."""

    model_config = ConfigDict(extra="ignore")

    version_id: str
    sequence: int
    upload_id: str
    generation: int
    expires_at: str | None = None
    upload_path: str | None = None
    upload_etag: str
    version_etag: str
    app_etag: str
    limits: dict[str, Any] = Field(default_factory=dict)


class HostedApplicationUploadReceipt(BaseModel):
    """Receipt of a stored artifact."""

    model_config = ConfigDict(extra="ignore")

    upload_id: str
    generation: int
    state: str
    received_bytes: int
    sha256: str
    upload_etag: str
    version_etag: str


class HostedApplicationVersionQueued(BaseModel):
    """Answer to completing an upload, configuring or retrying a version: validation is queued."""

    model_config = ConfigDict(extra="ignore")

    job_id: str | None = None
    state: str
    version_etag: str | None = None
    upload_etag: str | None = None


class HostedApplicationVersion(BaseModel):
    """A version of an application with its validation state."""

    model_config = ConfigDict(extra="ignore")

    id: str
    sequence: int
    filename: str | None = None
    artifact_kind: str | None = None
    expected_bytes: int | None = None
    validation_state: str = Field(
        description=(
            "uploading, queued, validating, awaiting_configuration, accepted, "
            "failed, rejected or canceled"
        )
    )
    security_state: str | None = None
    can_preview: bool = False
    can_activate: bool = False
    revision: int | None = None
    etag: str | None = None
    configuration_revision: int | None = None
    requested_configuration: dict[str, Any] = Field(default_factory=dict)
    candidate_manifest_digest: str | None = None
    upload: dict[str, Any] | None = None
    created_at: str | None = None
    job: dict[str, Any] | None = None
    accepted: dict[str, Any] | None = None


class HostedApplicationVersionList(BaseModel):
    """One page of versions, newest first."""

    model_config = ConfigDict(extra="ignore")

    items: list[HostedApplicationVersion] = Field(default_factory=list)
    next_cursor: str | None = None


class HostedApplicationValidationReport(BaseModel):
    """Validation report of a version: detected options, findings and the rejection code."""

    model_config = ConfigDict(extra="ignore")

    state: str
    job_id: str | None = None
    phase: str | None = None
    candidate_manifest_digest: str | None = None
    roots: list[str] = Field(default_factory=list)
    entries: list[str] = Field(default_factory=list)
    warnings: list[Any] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    configuration_revision: int | None = None
    file_count: int = 0
    expanded_bytes: int = 0
    next_offset: int | None = None
    error_code: str | None = None
    scanner: Any = None
    policy_version: str | None = None
    etag: str | None = None


class HostedApplicationLaunch(BaseModel):
    """Launch ticket: the form a browser posts to the content origin to open a version."""

    model_config = ConfigDict(extra="ignore")

    method: str
    version_id: str
    policy_version: str | None = None
    content_origin: str
    action: str
    ticket: str = Field(repr=False)
    issued_at: str | None = None
    expires_at: str | None = None


class HostedApplicationSharedWith(BaseModel):
    """People an application is shared with by name."""

    model_config = ConfigDict(extra="ignore")

    shared_with: list[dict[str, Any]] = Field(default_factory=list)


class HostedApplicationSharableUsers(BaseModel):
    """Directory users that can be granted access."""

    model_config = ConfigDict(extra="ignore")

    users: list[dict[str, Any]] = Field(default_factory=list)


class HostedApplicationShareLinkInfo(BaseModel):
    """A share link of an application."""

    model_config = ConfigDict(extra="ignore")

    id: str
    token: str = Field(repr=False)
    created_at: str | None = None


class HostedApplicationShareLink(BaseModel):
    """The live share link of an application, or none."""

    model_config = ConfigDict(extra="ignore")

    link: HostedApplicationShareLinkInfo | None = None


class HostedApplicationShareLinkTarget(BaseModel):
    """Answer to opening a share link: the application it leads to."""

    model_config = ConfigDict(extra="ignore")

    app_id: str


class HostedApplicationDeletion(BaseModel):
    """Answer to deleting an application: the purge is queued."""

    model_config = ConfigDict(extra="ignore")

    state: str
    job_id: str | None = None
    application: dict[str, Any] | None = None


class HostedApplicationDeletionStatus(BaseModel):
    """Progress of the purge of a deleted application."""

    model_config = ConfigDict(extra="ignore")

    state: str = Field(description="purging or purged")
    app_id: str
    remaining_prefixes: int = 0
    charged_bytes: int = 0
    etag: str | None = None
