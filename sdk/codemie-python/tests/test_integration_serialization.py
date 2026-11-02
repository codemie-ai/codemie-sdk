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

"""Serialization tests for Integration date fields."""

from datetime import datetime, timezone

from codemie_sdk.models.integration import CredentialTypes, Integration


def _make(**kwargs) -> Integration:
    return Integration(
        project_name="demo",
        credential_type=CredentialTypes.JIRA,
        credential_values=[],
        **kwargs,
    )


def test_undated_integration_serializes_null_dates():
    integration = _make()

    dumped = integration.model_dump()

    assert dumped["date"] is None
    assert dumped["update_date"] is None
    assert integration.model_dump_json()


def test_dated_integration_serializes_iso_strings():
    dt = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    dumped = _make(date=dt, update_date=dt).model_dump()

    assert dumped["date"] == dt.isoformat()
    assert dumped["update_date"] == dt.isoformat()
