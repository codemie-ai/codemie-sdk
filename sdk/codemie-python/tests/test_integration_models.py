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

"""Unit tests for the CredentialTypes enum and its parity with the Node.js SDK."""

import re
from pathlib import Path

import pytest

from codemie_sdk.models.integration import CredentialTypes

NODEJS_INTEGRATION_MODEL = (
    Path(__file__).resolve().parents[2]
    / "codemie-nodejs"
    / "src"
    / "models"
    / "integration.ts"
)


def _nodejs_credential_types() -> dict[str, str]:
    """Parse the ``CredentialTypes`` constant object from the Node.js SDK source."""
    source = NODEJS_INTEGRATION_MODEL.read_text()
    body = re.search(
        r"export const CredentialTypes = \{(.*?)\} as const;", source, re.DOTALL
    )
    assert body, f"CredentialTypes constant not found in {NODEJS_INTEGRATION_MODEL}"
    return dict(
        re.findall(r'^\s*(\w+):\s*"([^"]*)",?\s*$', body.group(1), re.MULTILINE)
    )


def test_zephyr_squad_is_removed():
    """ZephyrSquad was removed from the platform."""
    assert "ZEPHYR_SQUAD" not in CredentialTypes.__members__
    assert "ZephyrSquad" not in {member.value for member in CredentialTypes}


def test_ms_exchange_is_present():
    """MSExchange credential type mirrors the backend enum."""
    assert "MS_EXCHANGE" in CredentialTypes.__members__
    assert CredentialTypes.MS_EXCHANGE.value == "MSExchange"


@pytest.mark.skipif(
    not NODEJS_INTEGRATION_MODEL.exists(),
    reason="Node.js SDK sources are not checked out",
)
def test_credential_types_match_nodejs_sdk():
    """The Python and Node.js SDKs restate the backend enum by hand; they must not drift apart."""
    assert _nodejs_credential_types() == {
        member.name: member.value for member in CredentialTypes
    }
