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

"""Serialization tests for assistant models embedding undated integrations."""

from codemie_sdk.models.assistant import (
    MCPServerDetails,
    ToolDetails,
    ToolKitDetails,
)
from codemie_sdk.models.integration import CredentialTypes, Integration


def _undated() -> Integration:
    return Integration(
        project_name="demo",
        credential_type=next(iter(CredentialTypes)),
        credential_values=[],
    )


def test_tool_details_with_undated_integration_serializes():
    tool = ToolDetails(name="t", settings=_undated())

    assert tool.model_dump_json()


def test_toolkit_details_with_undated_integration_serializes():
    toolkit = ToolKitDetails(
        toolkit="kit", tools=[ToolDetails(name="t")], settings=_undated()
    )

    assert toolkit.model_dump_json()


def test_mcp_server_details_with_undated_integration_serializes():
    server = MCPServerDetails(
        name="srv", description=None, enabled=True, settings=_undated()
    )

    assert server.model_dump_json()


def test_exclude_none_omits_unset_dates():
    assert "date" not in _undated().model_dump(exclude_none=True)
    assert "update_date" not in _undated().model_dump(exclude_none=True)

    dumped = ToolDetails(name="t", settings=_undated()).model_dump(exclude_none=True)

    assert "date" not in dumped["settings"]
    assert "update_date" not in dumped["settings"]
