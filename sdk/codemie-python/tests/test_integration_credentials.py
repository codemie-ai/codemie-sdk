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

"""Drift test: credential key and option enums must match the committed snapshot."""

import copy
import json
from enum import Enum
from pathlib import Path

from codemie_sdk.models.integration import CredentialTypes
from codemie_sdk.models.integration_credentials import KEY_ENUMS, OPTION_ENUMS

SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "credential_snapshot.json"

with SNAPSHOT_PATH.open(encoding="utf-8") as _fh:
    SNAPSHOT = json.load(_fh)


def _values(enum_cls: type[Enum]) -> set[str]:
    return {member.value for member in enum_cls}


def _set_diff(label: str, expected: set, actual: set) -> list[str]:
    """Report names present on only one side."""
    problems = []
    if expected - actual:
        problems.append(f"{label}: in snapshot only: {sorted(expected - actual)}")
    if actual - expected:
        problems.append(f"{label}: in enums only: {sorted(actual - expected)}")
    return problems


def compare_registries(snapshot: dict) -> list[str]:
    """Return a list of differences between the registries and a snapshot."""
    problems: list[str] = []
    types = snapshot["types"]

    snap_key_types = {name for name, entry in types.items() if entry.get("keys")}
    problems += _set_diff(
        "key enum types", snap_key_types, {t.value for t in KEY_ENUMS}
    )
    for cred_type, enum_cls in KEY_ENUMS.items():
        if cred_type.value in types:
            problems += _set_diff(
                f"{cred_type.value} keys",
                set(types[cred_type.value].get("keys", [])),
                _values(enum_cls),
            )

    snap_selects = {
        (name, key) for name, entry in types.items() for key in entry.get("selects", {})
    }
    problems += _set_diff(
        "option enum selects",
        snap_selects,
        {(t.value, key) for t, key in OPTION_ENUMS},
    )
    for (cred_type, key), enum_cls in OPTION_ENUMS.items():
        select = types.get(cred_type.value, {}).get("selects", {}).get(key)
        if select is not None:
            problems += _set_diff(
                f"{cred_type.value}.{key} options",
                set(select["options"]),
                _values(enum_cls),
            )
    return problems


def test_registries_match_snapshot():
    assert compare_registries(SNAPSHOT) == []


def test_type_name_map_is_explicit_and_valid():
    name_map = SNAPSHOT["type_name_map"]
    assert name_map == {
        "OPEN_API": "OPENAPI",
        "FILE_SYSTEM": "FILESYSTEM",
        "SERVICENOW": "SERVICE_NOW",
        "ENVIRONMENT_VARS": "MCP",
    }
    for target in name_map.values():
        assert target in CredentialTypes.__members__


def test_snapshot_types_are_sdk_values():
    sdk_values = {t.value for t in CredentialTypes}
    assert set(SNAPSHOT["types"]) <= sdk_values


def test_detects_extra_key_on_one_side():
    mutated = copy.deepcopy(SNAPSHOT)
    mutated["types"]["MSExchange"]["keys"].append("brand_new_key")
    assert any("brand_new_key" in p for p in compare_registries(mutated))


def test_detects_removed_option():
    mutated = copy.deepcopy(SNAPSHOT)
    mutated["types"]["MSExchange"]["selects"]["auth_type"]["options"].remove("ntlm")
    assert any("ntlm" in p for p in compare_registries(mutated))


def test_detects_extra_type():
    mutated = copy.deepcopy(SNAPSHOT)
    mutated["types"]["Jira"] = {"keys": ["url"]}
    assert any("Jira" in p for p in compare_registries(mutated))


NO_KEY_SET = {
    CredentialTypes.PLUGIN,
    CredentialTypes.FILESYSTEM,
    CredentialTypes.SCHEDULER,
    CredentialTypes.WEBHOOK,
    CredentialTypes.DIAL,
    CredentialTypes.A2A,
    CredentialTypes.MCP,
    CredentialTypes.LITE_LLM,
    CredentialTypes.GOOGLE_OAUTH,
    CredentialTypes.MS_TEAMS,
}


def test_every_credential_type_has_key_enum_or_is_listed_without_one():
    covered = set(KEY_ENUMS) | NO_KEY_SET
    assert covered == set(CredentialTypes)
    assert not set(KEY_ENUMS) & NO_KEY_SET


def test_enums_exported_at_top_level():
    import codemie_sdk
    from codemie_sdk.models import integration_credentials as module

    expected = {"KEY_ENUMS", "OPTION_ENUMS", "CredentialTypes", "CredentialValues"}
    expected |= set(enum_cls.__name__ for enum_cls in KEY_ENUMS.values())
    expected |= set(enum_cls.__name__ for enum_cls in OPTION_ENUMS.values())
    for name in expected:
        assert hasattr(codemie_sdk, name), name
        assert name in codemie_sdk.__all__, name
    assert codemie_sdk.KEY_ENUMS is module.KEY_ENUMS
    assert codemie_sdk.OPTION_ENUMS is module.OPTION_ENUMS


def test_members_behave_as_plain_strings():
    from codemie_sdk.models.integration_credentials import ExchangeKeys

    assert str(ExchangeKeys.MAILBOX) == "mailbox"
    assert f"{ExchangeKeys.MAILBOX}" == "mailbox"
    assert ExchangeKeys.MAILBOX == "mailbox"


def test_registries_are_read_only():
    import pytest

    with pytest.raises(TypeError):
        KEY_ENUMS[CredentialTypes.JIRA] = None
    with pytest.raises(TypeError):
        OPTION_ENUMS[(CredentialTypes.JIRA, "auth_type")] = None
