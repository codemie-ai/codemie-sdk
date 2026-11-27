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

"""Credential key and select-option enums for integration types.

Each ``<Type>Keys`` enum lists the credential keys the platform accepts for an
integration type, and each ``<Type><KeyName>Options`` enum lists the stored
values of a select field. Members are ``str`` enums, so they serialize exactly
like plain strings and ``CredentialValues.key`` stays a ``str``.

Two registries map enums to integration types: ``KEY_ENUMS`` and
``OPTION_ENUMS``. A drift test compares them with a committed snapshot of the
platform's key sets (``tests/data/credential_snapshot.json``).

Export decision: all enums and both registries are re-exported from
``codemie_sdk``. The module stays single-file while it is under ~800 lines.
"""

from enum import Enum

from .integration import CredentialTypes


class ExchangeKeys(str, Enum):
    """Credential keys of the MS Exchange integration."""

    AUTH_TYPE = "auth_type"
    MAILBOX = "mailbox"
    EWS_URL = "ews_url"
    SERVICE_ACCOUNT_USERNAME = "service_account_username"
    SERVICE_ACCOUNT_PASSWORD = "service_account_password"
    OAUTH_TENANT_ID = "oauth_tenant_id"
    OAUTH_CLIENT_ID = "oauth_client_id"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"


class ExchangeAuthTypeOptions(str, Enum):
    """Stored values of the MS Exchange ``auth_type`` select."""

    NTLM = "ntlm"
    OAUTH_AZURE = "oauth_azure"


KEY_ENUMS: dict[CredentialTypes, type[Enum]] = {
    CredentialTypes.MS_EXCHANGE: ExchangeKeys,
}

OPTION_ENUMS: dict[tuple[CredentialTypes, str], type[Enum]] = {
    (CredentialTypes.MS_EXCHANGE, "auth_type"): ExchangeAuthTypeOptions,
}
