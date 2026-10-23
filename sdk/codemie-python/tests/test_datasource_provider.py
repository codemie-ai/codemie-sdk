import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from unittest.mock import MagicMock

from codemie_sdk.models.datasource import (
    CodeAnalysisDataSourceRequest,
    CodeExplorationDataSourceRequest,
    DataSource,
    ProviderDataSourceRequest,
    UpdateProviderDataSourceRequest,
    UpdateSvnDataSourceRequest,
)
from codemie_sdk.services.datasource import DatasourceService


def _service():
    service = DatasourceService("http://x", "tok")
    service._api = MagicMock()
    return service


def test_update_provider_puts_description_visibility_and_settings():
    service = _service()
    request = UpdateProviderDataSourceRequest(
        name="prov",
        project_name="proj",
        description="new desc",
        project_space_visible=True,
        settings={"repo": "r", "depth": 2},
    )
    service.update_provider_datasource("abc", request)
    call = service._api.put.call_args
    assert call.args[0] == "/v1/index/provider/abc"
    assert call.kwargs["json_data"] == {
        "name": "prov",
        "project_name": "proj",
        "description": "new desc",
        "project_space_visible": True,
        "repo": "r",
        "depth": 2,
    }


def test_update_provider_body_always_has_the_fields_the_backend_writes():
    # The backend sets name, project_name, description and project_space_visible
    # from the body on every update, with no None check.
    service = _service()
    request = UpdateProviderDataSourceRequest(
        name="prov",
        project_name="proj",
        description="d",
        project_space_visible=False,
        settings={},
    )
    service.update_provider_datasource("abc", request)
    body = service._api.put.call_args.kwargs["json_data"]
    assert body == {
        "name": "prov",
        "project_name": "proj",
        "description": "d",
        "project_space_visible": False,
    }


@pytest.mark.parametrize("missing", ["name", "project_name"])
def test_update_provider_without_name_or_project_name_is_rejected(missing):
    fields = {
        "name": "prov",
        "project_name": "proj",
        "description": "d",
        "project_space_visible": False,
    }
    del fields[missing]
    with pytest.raises(ValidationError, match=missing):
        UpdateProviderDataSourceRequest(**fields)


def test_create_typed_provider_posts_query_params():
    service = _service()
    request = ProviderDataSourceRequest(
        name="n",
        project_name="p",
        provider_name="prov",
        toolkit_id="tk",
        description="d",
        project_space_visible=False,
        settings={"k": "v"},
    )
    service.create_provider_datasource(request=request)
    call = service._api.post.call_args
    assert call.args[0] == "/v1/index/provider?toolkit_id=tk&provider_name=prov"
    assert call.kwargs["json_data"] == {
        "description": "d",
        "project_space_visible": False,
        "name": "n",
        "project_name": "p",
        "k": "v",
    }


def test_legacy_create_provider_still_works():
    service = _service()
    request = CodeAnalysisDataSourceRequest(
        name="n", project_name="p", api_url="u", access_token="t"
    )
    service.create_provider_datasource("tk", "prov", request)
    call = service._api.post.call_args
    assert call.args[0] == "/v1/index/provider?toolkit_id=tk&provider_name=prov"
    assert call.kwargs["json_data"]["name"] == "n"


@pytest.mark.parametrize(
    "request_",
    [
        CodeAnalysisDataSourceRequest(
            name="n", project_name="p", api_url="u", access_token="t"
        ),
        CodeExplorationDataSourceRequest(
            name="n", project_name="p", code_analysis_datasource_ids=["1"]
        ),
    ],
    ids=["code_analysis", "code_exploration"],
)
def test_legacy_provider_create_sends_the_keys_the_backend_reads(request_):
    # The backend provider create reads project_space_visible (snake_case) and
    # builds IndexInfo from it and from description, so neither may be missing.
    service = _service()
    service.create_provider_datasource("tk", "prov", request_)
    body = service._api.post.call_args.kwargs["json_data"]
    assert body["project_space_visible"] is False
    assert "projectSpaceVisible" not in body
    assert body["description"] == ""


def test_legacy_provider_create_sends_an_explicit_visibility_and_description():
    service = _service()
    request = CodeAnalysisDataSourceRequest(
        name="n",
        project_name="p",
        description="d",
        project_space_visible=True,
        api_url="u",
        access_token="t",
    )
    service.create_provider_datasource("tk", "prov", request)
    body = service._api.post.call_args.kwargs["json_data"]
    assert body["project_space_visible"] is True
    assert body["description"] == "d"


def test_datasource_exposes_typed_provider():
    now = datetime.now(timezone.utc).isoformat()
    ds = DataSource.model_validate(
        {
            "id": "1",
            "project_name": "p",
            "repo_name": "n",
            "index_type": "provider",
            "completed": True,
            "created_by": {"user_id": "u", "username": "u", "name": "u"},
            "update_date": now,
            "user_abilities": [],
            "provider_fields": {
                "provider_id": "pid",
                "toolkit_id": "tk",
                "base_params": {"token": "**********"},
                "create_params": {"x": 1},
            },
        }
    )
    assert ds.provider.toolkit_id == "tk"
    assert ds.provider.base_params == {"token": "**********"}


def test_create_provider_query_values_are_url_encoded():
    service = _service()
    request = ProviderDataSourceRequest(
        provider_name="p&x=1#",
        toolkit_id="a/../b?c",
        name="n",
        project_name="p",
        description="d",
        project_space_visible=False,
    )
    service.create_provider_datasource(request=request)
    endpoint = service._api.post.call_args.args[0]
    assert (
        endpoint
        == "/v1/index/provider?toolkit_id=a%2F..%2Fb%3Fc&provider_name=p%26x%3D1%23"
    )


def test_update_provider_path_segment_is_url_encoded():
    service = _service()
    request = UpdateProviderDataSourceRequest(
        name="prov",
        project_name="proj",
        description="d",
        project_space_visible=False,
        settings={},
    )
    service.update_provider_datasource("../x?y#", request)
    assert service._api.put.call_args.args[0] == "/v1/index/provider/..%2Fx%3Fy%23"


def test_update_svn_name_segment_is_url_encoded():
    service = _service()
    service.update(
        "id1",
        UpdateSvnDataSourceRequest(
            name="a-b",
            project_name="p/q",
            description="d",
            shared_with_project=True,
            prompt=None,
            files_filter=None,
            docs_generation=None,
        ),
    )
    assert service._api.put.call_args.args[0] == "/v1/application/p%2Fq/index/svn/a-b"


def test_create_provider_requires_top_level_name_and_project_name():
    with pytest.raises(ValidationError, match="name"):
        ProviderDataSourceRequest(
            provider_name="prov",
            toolkit_id="tk",
            description="d",
            project_space_visible=False,
        )


def test_create_provider_without_toolkit_or_provider_name_fails_before_http():
    service = _service()
    request = CodeAnalysisDataSourceRequest(
        name="ca",
        project_name="p",
        description="d",
        code_analysis_datasource_ids=["1"],
        api_url="http://x",
        access_token="t",
    )
    with pytest.raises(ValueError, match="toolkit_id and provider_name"):
        service.create_provider_datasource(request=request)
    service._api.post.assert_not_called()


def test_create_provider_explicit_empty_toolkit_id_is_not_overridden():
    service = _service()
    request = ProviderDataSourceRequest(
        provider_name="prov",
        toolkit_id="tk",
        name="n",
        project_name="p",
        description="d",
        project_space_visible=False,
    )
    with pytest.raises(ValueError):
        service.create_provider_datasource(toolkit_id="", request=request)
    service._api.post.assert_not_called()


def test_provider_request_and_update_request_share_a_base_not_each_other():
    assert not issubclass(ProviderDataSourceRequest, UpdateProviderDataSourceRequest)


def test_create_provider_argument_differing_from_request_raises():
    service = _service()
    request = ProviderDataSourceRequest(
        name="n",
        project_name="p",
        provider_name="prov",
        toolkit_id="tk",
        description="d",
        project_space_visible=False,
    )
    with pytest.raises(ValueError, match="toolkit_id"):
        service.create_provider_datasource(toolkit_id="other", request=request)
    service._api.post.assert_not_called()


def test_create_provider_matching_argument_is_accepted():
    service = _service()
    request = ProviderDataSourceRequest(
        name="n",
        project_name="p",
        provider_name="prov",
        toolkit_id="tk",
        description="d",
        project_space_visible=False,
    )
    service.create_provider_datasource(
        toolkit_id="tk", provider_name="prov", request=request
    )
    assert service._api.post.call_count == 1
