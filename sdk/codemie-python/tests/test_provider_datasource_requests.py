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

"""Unit tests for the provider datasource request models."""

import pytest

from codemie_sdk.models.datasource import (
    CodeAnalysisDataSourceRequest,
    CodeExplorationDataSourceRequest,
)

ANALYSIS_FIELDS = {
    "name": "ds",
    "project_name": "proj",
    "api_url": "https://example.com/repo.git",
    "access_token": "token",
}
EXPLORATION_FIELDS = {
    "name": "ds",
    "project_name": "proj",
    "code_analysis_datasource_ids": ["id-1"],
}

REQUESTS = [
    pytest.param(CodeAnalysisDataSourceRequest, ANALYSIS_FIELDS, id="code-analysis"),
    pytest.param(
        CodeExplorationDataSourceRequest, EXPLORATION_FIELDS, id="code-exploration"
    ),
]


@pytest.mark.parametrize("model, fields", REQUESTS)
@pytest.mark.parametrize("value", [True, False])
def test_project_space_visible_is_sent_in_snake_case(model, fields, value):
    request = model(**fields, project_space_visible=value)

    payload = request.model_dump(by_alias=True, exclude_none=True)

    assert payload["project_space_visible"] is value
    assert "projectSpaceVisible" not in payload


@pytest.mark.parametrize("model, fields", REQUESTS)
def test_project_space_visible_defaults_to_false_in_payload(model, fields):
    payload = model(**fields).model_dump(by_alias=True, exclude_none=True)

    assert payload["project_space_visible"] is False
    assert "projectSpaceVisible" not in payload
