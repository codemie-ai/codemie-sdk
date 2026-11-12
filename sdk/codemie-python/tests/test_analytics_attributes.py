import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from codemie_sdk.models.analytics import (
    AssistantsRequestsQueryParams,
    AttributesAnalyticsQueryParams,
    AttributesUsageQueryParams,
    PaginatedAnalyticsQueryParams,
)
from codemie_sdk.services.analytics import AnalyticsService

BASE = "https://api.example.com"

TABULAR_BODY = {
    "data": {"columns": [], "rows": []},
    "metadata": {
        "timestamp": "t",
        "data_as_of": "t",
        "filters_applied": {},
        "execution_time_ms": 1,
    },
}


def _ok_response(body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body
    return response


def _call(method_name: str, *args):
    service = AnalyticsService(BASE, "token")
    with patch("codemie_sdk.utils.http.requests.get") as get:
        get.return_value = _ok_response(TABULAR_BODY)
        getattr(service, method_name)(*args)
    return get.call_args.kwargs


def test_assistants_chats_sends_attributes_as_json_string():
    kwargs = _call(
        "get_assistants_chats",
        AttributesAnalyticsQueryParams(attributes={"team": "alpha"}),
    )

    assert kwargs["url"].endswith("/v1/analytics/assistants-chats")
    assert isinstance(kwargs["params"]["attributes"], str)
    assert json.loads(kwargs["params"]["attributes"]) == {"team": "alpha"}


def test_workflows_sends_attributes_as_json_string():
    kwargs = _call(
        "get_workflows",
        AttributesAnalyticsQueryParams(attributes={"team": "alpha"}),
    )

    assert kwargs["url"].endswith("/v1/analytics/workflows")
    assert isinstance(kwargs["params"]["attributes"], str)
    assert json.loads(kwargs["params"]["attributes"]) == {"team": "alpha"}


def test_attributes_roundtrip_non_ascii_and_quotes():
    value = {"team": 'ålpha "x"'}
    kwargs = _call(
        "get_assistants_chats", AttributesAnalyticsQueryParams(attributes=value)
    )

    assert json.loads(kwargs["params"]["attributes"]) == value


def test_attributes_omitted_when_none():
    kwargs = _call("get_assistants_chats", AttributesAnalyticsQueryParams())

    assert "attributes" not in kwargs["params"]
    assert kwargs["params"]["page"] == 0
    assert kwargs["params"]["per_page"] == 20


def test_empty_attributes_sends_empty_object_string():
    kwargs = _call("get_workflows", AttributesAnalyticsQueryParams(attributes={}))

    assert kwargs["params"]["attributes"] == "{}"


def test_assistants_requests_endpoint_and_params():
    kwargs = _call(
        "get_assistants_requests",
        AssistantsRequestsQueryParams(
            client_source="platform",
            assistant_id="a1",
            attributes={"team": "alpha"},
        ),
    )

    assert kwargs["url"] == f"{BASE}/v1/analytics/assistants-requests"
    assert kwargs["params"]["client_source"] == "platform"
    assert kwargs["params"]["assistant_id"] == "a1"
    assert json.loads(kwargs["params"]["attributes"]) == {"team": "alpha"}


def test_workflows_executions_endpoint():
    kwargs = _call(
        "get_workflows_executions",
        AttributesAnalyticsQueryParams(
            client_source="other", attributes={"team": "alpha"}
        ),
    )

    assert kwargs["url"] == f"{BASE}/v1/analytics/workflows-executions"
    assert kwargs["params"]["client_source"] == "other"
    assert json.loads(kwargs["params"]["attributes"]) == {"team": "alpha"}


def test_attributes_usage_requires_attribute_key():
    with pytest.raises(ValidationError):
        AttributesUsageQueryParams()


def test_attributes_usage_endpoint_and_params():
    kwargs = _call(
        "get_attributes_usage",
        AttributesUsageQueryParams(attribute_key="team", attributes={"env": "prod"}),
    )

    assert kwargs["url"] == f"{BASE}/v1/analytics/attributes-usage"
    assert kwargs["params"]["attribute_key"] == "team"
    assert json.loads(kwargs["params"]["attributes"]) == {"env": "prod"}


def test_shared_paginated_params_has_no_attributes_field():
    assert "attributes" not in PaginatedAnalyticsQueryParams.model_fields

    kwargs = _call("get_tools_usage", PaginatedAnalyticsQueryParams())

    assert "attributes" not in kwargs["params"]


def test_new_symbols_exported_from_package_root():
    from codemie_sdk import (  # noqa: F401
        AssistantsRequestsQueryParams as A,
        AttributesAnalyticsQueryParams as B,
        AttributesUsageQueryParams as C,
    )
