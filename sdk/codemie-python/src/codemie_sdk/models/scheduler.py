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

"""Scheduler models for the CodeMie SDK."""

from pydantic import BaseModel, ConfigDict, Field


class SchedulerResourceRef(BaseModel):
    """The assistant, workflow or datasource a scheduler runs."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    type: str


class SchedulerProjectRef(BaseModel):
    """The project a scheduler belongs to."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class SchedulerSchedule(BaseModel):
    """When a scheduler runs."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    cron: str
    description: str
    timezone: str
    next_run_at: str | None = Field(default=None, alias="nextRunAt")


class SchedulerLastRun(BaseModel):
    """The latest run of a scheduler."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    status: str
    started_at: str = Field(alias="startedAt")


class SchedulerListItem(BaseModel):
    """One scheduler row of the list."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    resource: SchedulerResourceRef
    project: SchedulerProjectRef
    schedule: SchedulerSchedule
    is_enabled: bool = Field(alias="isEnabled")
    last_run: SchedulerLastRun | None = Field(default=None, alias="lastRun")


class SchedulerPagination(BaseModel):
    """Pagination metadata of the scheduler list."""

    model_config = ConfigDict(extra="ignore")

    page: int
    per_page: int
    total: int
    pages: int


class SchedulerListResponse(BaseModel):
    """Paginated scheduler list."""

    model_config = ConfigDict(extra="ignore")

    items: list[SchedulerListItem]
    pagination: SchedulerPagination
