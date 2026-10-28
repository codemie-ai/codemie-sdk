import pytest
import requests

from codemie_sdk.models.toolkit_policy import ApprovedToolkit
from codemie_sdk.services.toolkit_policy import ToolkitPolicyService

FLAG = {"id": "features:toolkitManagement", "settings": {"enabled": True}}
FLAG_DISABLED = {"id": "features:toolkitManagement", "settings": {"enabled": False}}


class DummyConfig:
    def __init__(self, components):
        self.components = components

    def get_config(self):
        return self.components


class DummyApi:
    def __init__(self, policy=None, error=None):
        self.policy = policy
        self.error = error
        self.calls = []

    def get(self, endpoint, response_model, wrap_response=True):
        self.calls.append(("GET", endpoint))
        if self.error:
            raise self.error
        return self.policy

    def put(self, endpoint, response_model, json_data, wrap_response=True):
        self.calls.append(("PUT", endpoint, json_data))
        if self.error:
            raise self.error
        return json_data


def make_service(components, api):
    service = ToolkitPolicyService("https://api.example.com", "token")
    service._config = DummyConfig(components)
    service._api = api
    return service


def test_flag_off_does_not_call_policy_endpoint():
    api = DummyApi()
    policy = make_service([{"id": "chatDisclaimer"}], api).get_policy()
    assert (policy.flag_enabled, policy.in_effect, policy.approved_toolkits) == (
        False,
        False,
        None,
    )
    assert api.calls == []


@pytest.mark.parametrize(
    "component",
    [
        FLAG_DISABLED,
        {"id": "features:toolkitManagement", "settings": {}},
        {"id": "features:toolkitManagement"},
    ],
)
def test_flag_present_but_not_enabled_is_off(component):
    api = DummyApi({"approved_toolkits": [{"toolkit": "Git", "tools": None}]})
    policy = make_service([component], api).get_policy()
    assert (policy.flag_enabled, policy.in_effect, policy.approved_toolkits) == (
        False,
        False,
        None,
    )
    assert api.calls == []


def test_flag_on_with_empty_policy():
    api = DummyApi({"approved_toolkits": []})
    policy = make_service([FLAG], api).get_policy()
    assert policy.flag_enabled is True
    assert policy.in_effect is False
    assert policy.approved_toolkits == []


def test_restrictive_policy_preserves_tools():
    api = DummyApi(
        {
            "approved_toolkits": [
                {"toolkit": "Git", "tools": None},
                {"toolkit": "FileSystem", "tools": ["read_file"]},
            ]
        }
    )
    policy = make_service([FLAG], api).get_policy()
    assert policy.in_effect is True
    assert policy.approved_toolkits[0].tools is None
    assert policy.approved_toolkits[1].tools == ["read_file"]
    assert api.calls == [("GET", "/v1/toolkit-management/policy")]


def test_set_policy_body_keeps_null_tools():
    api = DummyApi()
    result = make_service([FLAG], api).set_policy(
        [ApprovedToolkit(toolkit="Git"), ApprovedToolkit(toolkit="FS", tools=["a"])]
    )
    assert api.calls[0][2] == {
        "approved_toolkits": [
            {"toolkit": "Git", "tools": None},
            {"toolkit": "FS", "tools": ["a"]},
        ]
    }
    assert result.flag_enabled is True and result.in_effect is True


def test_set_empty_policy_sends_empty_list():
    api = DummyApi()
    result = make_service([FLAG], api).set_policy([])
    assert api.calls[0][2] == {"approved_toolkits": []}
    assert result.in_effect is False


def test_403_propagates_as_http_error():
    api = DummyApi(error=requests.HTTPError("403"))
    with pytest.raises(requests.HTTPError):
        make_service([FLAG], api).get_policy()


def test_put_400_propagates_as_http_error():
    api = DummyApi(error=requests.HTTPError("400"))
    with pytest.raises(requests.HTTPError):
        make_service([FLAG], api).set_policy([ApprovedToolkit(toolkit="Git")])


def test_client_registers_toolkit_policy():
    import inspect

    from codemie_sdk.client import client as client_module

    assert "self.toolkit_policy = ToolkitPolicyService(" in inspect.getsource(
        client_module
    )