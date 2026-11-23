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

"""Unit tests for display_name support in project Pydantic models."""

import pytest
from pydantic import ValidationError

from codemie_sdk.models.project import (
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectDetailResponse,
    ProjectListItem,
    ProjectUpdateRequest,
)


class TestProjectListItemDisplayName:
    def test_accepts_display_name(self):
        item = ProjectListItem(
            name="p",
            display_name="My Project",
            project_type="shared",
            user_count=0,
            admin_count=0,
        )
        assert item.display_name == "My Project"

    def test_display_name_defaults_to_none(self):
        item = ProjectListItem(
            name="p", project_type="shared", user_count=0, admin_count=0
        )
        assert item.display_name is None

    def test_display_name_can_be_null(self):
        item = ProjectListItem(
            name="p",
            display_name=None,
            project_type="shared",
            user_count=0,
            admin_count=0,
        )
        assert item.display_name is None

    def test_extra_fields_ignored(self):
        item = ProjectListItem(
            name="p",
            project_type="shared",
            user_count=0,
            admin_count=0,
            unknown_field="x",
        )
        assert not hasattr(item, "unknown_field")


class TestProjectDetailResponseDisplayName:
    def test_accepts_display_name(self):
        resp = ProjectDetailResponse(
            name="p",
            display_name="Detail Display",
            project_type="shared",
            user_count=1,
            admin_count=1,
            members=[],
        )
        assert resp.display_name == "Detail Display"

    def test_display_name_defaults_to_none(self):
        resp = ProjectDetailResponse(
            name="p", project_type="shared", user_count=1, admin_count=1, members=[]
        )
        assert resp.display_name is None


class TestProjectCreateRequestDisplayName:
    def test_accepts_display_name(self):
        req = ProjectCreateRequest(
            name="p", description="d", display_name="Pretty Name"
        )
        assert req.display_name == "Pretty Name"

    def test_display_name_defaults_to_none(self):
        req = ProjectCreateRequest(name="p", description="d")
        assert req.display_name is None

    def test_display_name_max_length_150_is_valid(self):
        req = ProjectCreateRequest(name="p", description="d", display_name="a" * 150)
        assert len(req.display_name) == 150

    def test_display_name_exceeds_150_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(name="p", description="d", display_name="x" * 151)


class TestProjectCreateResponseDisplayName:
    def test_accepts_display_name(self):
        from datetime import datetime, UTC

        resp = ProjectCreateResponse(
            name="p",
            display_name="Resp Display",
            description="d",
            project_type="shared",
            created_by="user-1",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert resp.display_name == "Resp Display"

    def test_display_name_defaults_to_none(self):
        from datetime import datetime, UTC

        resp = ProjectCreateResponse(
            name="p",
            description="d",
            project_type="shared",
            created_by="user-1",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert resp.display_name is None


class TestProjectUpdateRequestDisplayName:
    def test_accepts_display_name(self):
        req = ProjectUpdateRequest(display_name="New Name")
        assert req.display_name == "New Name"

    def test_display_name_defaults_to_none(self):
        req = ProjectUpdateRequest()
        assert req.display_name is None

    def test_display_name_max_length_150_is_valid(self):
        req = ProjectUpdateRequest(display_name="b" * 150)
        assert len(req.display_name) == 150

    def test_display_name_exceeds_150_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ProjectUpdateRequest(display_name="y" * 151)


class TestProjectDetailInstanceId:
    def test_accepts_project_instance_id(self):
        detail = ProjectDetailResponse(
            name="p",
            project_instance_id="0b9f1c1e-3d6a-4a53-9b7c-7a3c2f6d1e11",
            project_type="shared",
            user_count=0,
            admin_count=0,
            members=[],
        )
        assert str(detail.project_instance_id) == "0b9f1c1e-3d6a-4a53-9b7c-7a3c2f6d1e11"

    def test_project_instance_id_defaults_to_none(self):
        detail = ProjectDetailResponse(
            name="p",
            project_type="shared",
            user_count=0,
            admin_count=0,
            members=[],
        )
        assert detail.project_instance_id is None
