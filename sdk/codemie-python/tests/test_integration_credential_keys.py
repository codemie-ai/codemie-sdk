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

"""Credential keys given as enum members reach the HTTP layer as plain strings."""

import json
from unittest.mock import MagicMock, patch

import pytest

from codemie_sdk.models.integration import (
    CredentialTypes,
    CredentialValues,
    Integration,
    IntegrationTestRequest,
    IntegrationTestResponse,
)
from codemie_sdk.models.integration_credentials import (
    ExchangeAuthTypeOptions,
    ExchangeKeys,
)
from codemie_sdk.services.integration import IntegrationService


@pytest.fixture
def service():
    return IntegrationService("https://api.example.com", "token")


def _values(use_enum: bool) -> list[CredentialValues]:
    key = ExchangeKeys.MAILBOX if use_enum else "mailbox"
    auth_key = ExchangeKeys.AUTH_TYPE if use_enum else "auth_type"
    auth_value = ExchangeAuthTypeOptions.NTLM if use_enum else "ntlm"
    return [
        CredentialValues(key=key, value="user@example.invalid"),
        CredentialValues(key=auth_key, value=auth_value),
    ]


def _integration(use_enum: bool) -> Integration:
    return Integration(
        project_name="demo",
        alias="demo-alias",
        credential_type=CredentialTypes.MS_EXCHANGE,
        credential_values=_values(use_enum),
    )


def _response():
    response = MagicMock()
    response.status_code = 200
    response.content = b"{}"
    response.json.return_value = {"message": "ok", "success": True}
    return response


def _captured_json(method: str, call) -> dict:
    with patch(
        f"codemie_sdk.utils.http.requests.{method}", return_value=_response()
    ) as mocked:
        call()
    return mocked.call_args.kwargs["json"]


def test_enum_key_dump_equals_plain_string_dump():
    enum_dump = CredentialValues(key=ExchangeKeys.MAILBOX, value="x").model_dump(
        mode="json"
    )
    plain_dump = CredentialValues(key="mailbox", value="x").model_dump(mode="json")
    assert enum_dump == plain_dump


@pytest.mark.parametrize("method", ["create", "update", "test"])
def test_enum_key_sent_as_plain_string(service, method):
    def invoke(use_enum: bool):
        if method == "create":
            return service.create(_integration(use_enum))
        if method == "update":
            return service.update("id-1", _integration(use_enum))
        request = IntegrationTestRequest(
            credential_type=CredentialTypes.MS_EXCHANGE.value,
            credential_values=_values(use_enum),
        )
        return service.test(request, IntegrationTestResponse)

    http_method = "put" if method == "update" else "post"
    with_enum = _captured_json(http_method, lambda: invoke(True))
    with_plain = _captured_json(http_method, lambda: invoke(False))

    assert with_enum == with_plain
    round_trip = json.loads(json.dumps(with_enum))
    entries = round_trip["credential_values"]
    assert all(type(entry["key"]) is str for entry in entries)
    assert [entry["key"] for entry in entries] == ["mailbox", "auth_type"]
    assert entries[1]["value"] == "ntlm"
    assert type(entries[1]["value"]) is str


def test_unknown_string_key_is_accepted():
    assert CredentialValues(key="mailbxo", value="x").key == "mailbxo"
