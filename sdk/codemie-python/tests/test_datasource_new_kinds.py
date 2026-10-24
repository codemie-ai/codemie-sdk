from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from codemie_sdk.models.datasource import (
    DataSource,
    DataSourceType,
    SharePointDataSourceRequest,
    SvnDataSourceRequest,
    UpdateSharePointDataSourceRequest,
    UpdateSvnDataSourceRequest,
    UpdateXrayDataSourceRequest,
    XrayDataSourceRequest,
)
from codemie_sdk.services.datasource import DatasourceService

COMMON = {"name": "my-ds", "project_name": "proj", "description": "d"}
# The SVN update must state what the backend writes on every PUT.
SVN_STATE = {
    "shared_with_project": False,
    "prompt": None,
    "files_filter": None,
    "docs_generation": None,
}


def _service():
    service = DatasourceService("http://x", "tok")
    service._api = MagicMock()
    return service


def test_svn_requires_link_and_makes_no_http_call():
    service = _service()
    with pytest.raises(ValidationError, match="link"):
        SvnDataSourceRequest(**COMMON)
    service._api.post.assert_not_called()


def test_sharepoint_requires_site_url():
    with pytest.raises(ValidationError, match="site_url"):
        SharePointDataSourceRequest(**COMMON)


def test_xray_requires_jql():
    with pytest.raises(ValidationError, match="jql"):
        XrayDataSourceRequest(**COMMON)


def test_sharepoint_rejects_oversized_file_limit():
    with pytest.raises(ValidationError, match="max_file_size_mb"):
        SharePointDataSourceRequest(
            **COMMON, site_url="https://x.sharepoint.com/s", max_file_size_mb=501
        )


def test_sharepoint_rejects_non_https_site_url():
    with pytest.raises(ValidationError, match="site_url"):
        SharePointDataSourceRequest(**COMMON, site_url="http://x.sharepoint.com/s")


def test_sharepoint_rejects_unknown_auth_type():
    with pytest.raises(ValidationError, match="auth_type"):
        SharePointDataSourceRequest(
            **COMMON, site_url="https://x.sharepoint.com/s", auth_type="basic"
        )


def test_svn_branch_defaults_to_trunk():
    request = SvnDataSourceRequest(**COMMON, link="svn://host/repo", index_type="code")
    assert request.branch == "trunk"
    assert request.type == DataSourceType.SVN


@pytest.mark.parametrize(
    "request_obj,path",
    [
        (
            SvnDataSourceRequest(**COMMON, link="svn://h/r", index_type="code"),
            "/v1/application/proj/index/svn",
        ),
        (
            SharePointDataSourceRequest(**COMMON, site_url="https://x.com/s"),
            "/v1/index/knowledge_base/sharepoint",
        ),
        (XrayDataSourceRequest(**COMMON, jql="p"), "/v1/index/knowledge_base/xray"),
    ],
)
def test_create_routes(request_obj, path):
    service = _service()
    service.create(request_obj)
    assert service._api.post.call_args.args[0] == path


@pytest.mark.parametrize(
    "request_obj,path",
    [
        (
            UpdateSvnDataSourceRequest(**COMMON, **SVN_STATE, link="svn://h/r"),
            "/v1/application/proj/index/svn/my-ds",
        ),
        (
            UpdateSharePointDataSourceRequest(**COMMON, site_url="https://x.com/s"),
            "/v1/index/knowledge_base/sharepoint",
        ),
        (
            UpdateXrayDataSourceRequest(**COMMON, jql="p"),
            "/v1/index/knowledge_base/xray",
        ),
    ],
)
def test_update_routes(request_obj, path):
    service = _service()
    service.update("id1", request_obj)
    assert service._api.put.call_args.args[0] == path


def _payload(index_type, **extra):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "1",
        "project_name": "proj",
        "repo_name": "n",
        "index_type": index_type,
        "completed": True,
        "created_by": {"user_id": "u", "username": "u", "name": "u"},
        "update_date": now,
        "date": now,
        "user_abilities": [],
        **extra,
    }


@pytest.mark.parametrize("index_type", ["code", "summary", "chunk-summary"])
def test_svn_datasource_is_read_by_vcs_type(index_type):
    ds = DataSource.model_validate(
        _payload(
            index_type,
            vcs_type="svn",
            link="svn://h/r",
            branch="trunk",
            files_filter="*.py",
            docs_generation=True,
        )
    )
    assert ds.svn.link == "svn://h/r"
    assert ds.svn.branch == "trunk"
    assert ds.svn.files_filter == "*.py"
    assert ds.svn.docs_generation is True
    assert ds.code.link == "svn://h/r"


def test_git_datasource_has_no_svn_sub_object():
    ds = DataSource.model_validate(
        _payload("code", vcs_type="git", link="https://g/r", branch="main")
    )
    assert ds.svn is None


def test_datasource_reads_nested_sharepoint_config():
    ds = DataSource.model_validate(
        _payload(
            "knowledge_base_sharepoint",
            sharepoint={
                "site_url": "https://x.com/s",
                "max_file_size_mb": 10,
                "auth_type": "integration",
                "access_token": "secret",
                "expires_at": 0,
            },
        )
    )
    assert ds.sharepoint.site_url == "https://x.com/s"
    assert ds.sharepoint.max_file_size_mb == 10
    assert ds.sharepoint.auth_type == "integration"
    assert not hasattr(ds.sharepoint, "access_token")


def test_datasource_reads_nested_xray_config():
    ds = DataSource.model_validate(
        _payload("knowledge_base_xray", xray={"jql": "project = X"})
    )
    assert ds.xray.jql == "project = X"


@pytest.mark.parametrize(
    "index_type, key",
    [
        ("knowledge_base_sharepoint", "sharepoint"),
        ("knowledge_base_xray", "xray"),
    ],
)
def test_read_without_nested_config_is_empty(index_type, key):
    ds = DataSource.model_validate(_payload(index_type))
    assert getattr(ds, key) is None


def test_read_partial_nested_config_succeeds():
    ds = DataSource.model_validate(_payload("knowledge_base_sharepoint", sharepoint={}))
    assert ds.sharepoint.site_url is None


def test_svn_create_requires_index_type():
    with pytest.raises(ValidationError, match="indexType"):
        SvnDataSourceRequest(**COMMON, link="svn://h/r")


def test_svn_create_sends_index_type():
    service = _service()
    service.create(SvnDataSourceRequest(**COMMON, link="svn://h/r", index_type="code"))
    assert service._api.post.call_args.kwargs["json_data"]["indexType"] == "code"


def test_svn_update_sends_camel_case_keys_the_backend_reads():
    service = _service()
    service.update(
        "id1",
        UpdateSvnDataSourceRequest(
            **COMMON,
            link="svn://h/r",
            prompt="p",
            files_filter="*.py",
            embeddings_model="emb",
            docs_generation=True,
            project_space_visible=True,
        ),
    )
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["filesFilter"] == "*.py"
    assert body["embeddingsModel"] == "emb"
    assert body["docsGeneration"] is True
    assert body["projectSpaceVisible"] is True
    assert "files_filter" not in body
    assert "docs_generation" not in body


def test_sharepoint_update_without_site_url_is_valid():
    request = UpdateSharePointDataSourceRequest(**COMMON)
    assert request.site_url is None


@pytest.mark.parametrize("auth_type", ["oauth_codemie", "oauth_custom"])
def test_sharepoint_oauth_requires_access_token(auth_type):
    with pytest.raises(ValidationError, match="access_token"):
        SharePointDataSourceRequest(
            **COMMON, site_url="https://x.sharepoint.com/s", auth_type=auth_type
        )


def test_sharepoint_oauth_with_access_token_is_sent():
    service = _service()
    service.create(
        SharePointDataSourceRequest(
            **COMMON,
            site_url="https://x.sharepoint.com/s",
            auth_type="oauth_codemie",
            access_token="tok",
        )
    )
    assert service._api.post.call_args.kwargs["json_data"]["access_token"] == "tok"


def test_datasource_exposes_schedule_fields():
    ds = DataSource.model_validate(
        _payload("code", link="svn://h/r", cron_expression="0 3 * * *", timezone="UTC")
    )
    assert ds.cron_expression == "0 3 * * *"
    assert ds.timezone == "UTC"


def test_datasource_without_schedule_has_empty_schedule_fields():
    ds = DataSource.model_validate(_payload("code", link="svn://h/r"))
    assert ds.cron_expression is None
    assert ds.timezone is None


@pytest.mark.parametrize("index_type", ["code", "summary", "chunk-summary"])
def test_code_sub_object_carries_all_backend_values(index_type):
    ds = DataSource.model_validate(
        _payload(
            index_type,
            link="https://git/r",
            branch="main",
            files_filter="*.py",
            embeddings_model="emb",
            summarization_model="sum",
            prompt="be brief",
            docs_generation=True,
        )
    )
    assert ds.code.link == "https://git/r"
    assert ds.code.branch == "main"
    assert ds.code.index_type.value == index_type
    assert ds.code.files_filter == "*.py"
    assert ds.code.embeddings_model == "emb"
    assert ds.code.summarization_model == "sum"
    assert ds.code.prompt == "be brief"
    assert ds.code.docs_generation is True


def test_code_sub_object_reads_list_item_without_branch():
    ds = DataSource.model_validate(_payload("code", link="https://git/r"))
    assert ds.code.link == "https://git/r"
    assert ds.code.branch is None


def test_code_sub_object_with_empty_branch_is_still_built():
    ds = DataSource.model_validate(_payload("code", link="https://git/r", branch=""))
    assert ds.code.link == "https://git/r"


def test_git_faq_sub_object_carries_embedding_model():
    ds = DataSource.model_validate(
        _payload(
            "knowledge_base_git_faq",
            link="https://git/r",
            branch="main",
            files_filter="*.md",
            embeddings_model="emb",
        )
    )
    assert ds.git_faq.embedding_model == "emb"
    assert ds.git_faq.files_filter == "*.md"


def test_git_faq_sub_object_reads_partial_payload():
    ds = DataSource.model_validate(_payload("knowledge_base_git_faq", branch="main"))
    assert ds.git_faq.branch == "main"
    assert ds.git_faq.link is None


def test_wrong_typed_sub_object_value_is_dropped_with_a_warning(caplog):
    with caplog.at_level("WARNING"):
        ds = DataSource.model_validate(
            _payload(
                "knowledge_base_sharepoint",
                sharepoint={"site_url": "https://x.com/s", "max_file_size_mb": "big"},
            )
        )
    assert ds.sharepoint is None
    assert "datasource 1" in caplog.text
    assert "sharepoint" in caplog.text


def test_null_provider_params_read_as_empty():
    ds = DataSource.model_validate(
        _payload(
            "provider", provider_fields={"create_params": None, "base_params": None}
        )
    )
    assert ds.provider.create_params == {}
    assert ds.provider.base_params == {}


def test_svn_update_shared_flag_is_sent_as_project_space_visible_camel_case():
    service = _service()
    service.update(
        "id1",
        UpdateSvnDataSourceRequest(
            **{**COMMON, **{**SVN_STATE, "shared_with_project": True}},
            link="svn://h/r",
        ),
    )
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["projectSpaceVisible"] is True
    assert "project_space_visible" not in body
    assert "shared_with_project" not in body


def test_svn_update_does_not_send_default_branch():
    service = _service()
    service.update(
        "id1", UpdateSvnDataSourceRequest(**COMMON, **SVN_STATE, link="svn://h/r")
    )
    assert "branch" not in service._api.put.call_args.kwargs["json_data"]


def test_svn_update_sends_explicit_branch():
    service = _service()
    service.update(
        "id1",
        UpdateSvnDataSourceRequest(
            **COMMON, **SVN_STATE, link="svn://h/r", branch="branches/release"
        ),
    )
    assert (
        service._api.put.call_args.kwargs["json_data"]["branch"] == "branches/release"
    )


@pytest.mark.parametrize(
    "request_cls, extra",
    [
        (SvnDataSourceRequest, {"link": "svn://h/r", "index_type": "code"}),
        (SharePointDataSourceRequest, {"site_url": "https://x.com/s"}),
        (XrayDataSourceRequest, {"jql": "project = X"}),
        (UpdateSvnDataSourceRequest, {"link": "svn://h/r"}),
        (UpdateSharePointDataSourceRequest, {}),
        (UpdateXrayDataSourceRequest, {"jql": "project = X"}),
    ],
)
def test_new_requests_reject_misspelled_field_names(request_cls, extra):
    with pytest.raises(ValidationError, match="Extra inputs"):
        request_cls(**COMMON, **extra, embedding_models="x")


def test_sharepoint_update_body_sends_only_what_was_set():
    service = _service()
    service.update(
        "id1",
        UpdateSharePointDataSourceRequest(**COMMON, include_lists=False),
    )
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["include_lists"] is False
    assert "site_url" not in body
    assert body["name"] == "my-ds"


def test_sharepoint_update_with_oauth_needs_no_access_token():
    request = UpdateSharePointDataSourceRequest(**COMMON, auth_type="oauth_codemie")
    assert request.access_token is None


def test_xray_update_body_carries_jql():
    service = _service()
    service.update("id1", UpdateXrayDataSourceRequest(**COMMON, jql="project = X"))
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["jql"] == "project = X"
    assert "embedding_model" not in body


def test_xray_update_rejects_embedding_model_the_backend_ignores():
    with pytest.raises(ValidationError, match="embedding_model"):
        UpdateXrayDataSourceRequest(**COMMON, jql="p", embedding_model="x")


def test_xray_create_still_takes_embedding_model():
    request = XrayDataSourceRequest(**COMMON, jql="p", embedding_model="x")
    assert request.embedding_model == "x"


def test_sharepoint_access_token_is_hidden_from_repr():
    request = SharePointDataSourceRequest(
        **COMMON,
        site_url="https://x.com/s",
        auth_type="oauth_custom",
        access_token="s3cret",
    )
    assert "s3cret" not in repr(request)


@pytest.mark.parametrize("value", [0, -1])
def test_sharepoint_file_size_limit_rejects_zero_and_negative(value):
    with pytest.raises(ValidationError, match="max_file_size_mb"):
        SharePointDataSourceRequest(
            **COMMON, site_url="https://x.com/s", max_file_size_mb=value
        )


# --- update requests state what the backend writes on every PUT ---------------------


@pytest.mark.parametrize(
    "missing", ["projectSpaceVisible", "prompt", "filesFilter", "docsGeneration"]
)
def test_svn_update_without_a_field_the_backend_always_writes_is_rejected(missing):
    # A missing visibility flag becomes True on the backend, a missing prompt,
    # filter or docs flag is wiped: the caller has to state each of them.
    fields = {
        **COMMON,
        "link": "svn://h/r",
        "projectSpaceVisible": True,
        "prompt": "p",
        "filesFilter": "*.py",
        "docsGeneration": True,
    }
    del fields[missing]
    with pytest.raises(ValidationError, match=missing):
        UpdateSvnDataSourceRequest(**fields)


def test_svn_update_accepts_none_for_the_nullable_fields_and_does_not_send_them():
    service = _service()
    service.update(
        "id1", UpdateSvnDataSourceRequest(**COMMON, **SVN_STATE, link="svn://h/r")
    )
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["projectSpaceVisible"] is False
    for key in ("prompt", "filesFilter", "docsGeneration"):
        assert key not in body


@pytest.mark.parametrize(
    "request_cls,extra",
    [
        (UpdateXrayDataSourceRequest, {"jql": "p"}),
        (UpdateSharePointDataSourceRequest, {"site_url": "https://x.com/s"}),
    ],
)
def test_xray_and_sharepoint_update_keep_the_stored_visibility_when_not_stated(
    request_cls, extra
):
    service = _service()
    service.update("id1", request_cls(**COMMON, **extra))
    body = service._api.put.call_args.kwargs["json_data"]
    assert "project_space_visible" not in body


@pytest.mark.parametrize(
    "request_cls,extra",
    [
        (UpdateXrayDataSourceRequest, {"jql": "p"}),
        (UpdateSharePointDataSourceRequest, {"site_url": "https://x.com/s"}),
    ],
)
def test_xray_and_sharepoint_update_send_a_stated_visibility(request_cls, extra):
    service = _service()
    service.update("id1", request_cls(**COMMON, **extra, shared_with_project=False))
    body = service._api.put.call_args.kwargs["json_data"]
    assert body["project_space_visible"] is False


# --- SharePoint: OAuth reindex needs the token ----------------------------------------


@pytest.mark.parametrize("auth_type", ["oauth_codemie", "oauth_custom"])
def test_sharepoint_oauth_full_reindex_without_a_token_is_rejected(auth_type):
    with pytest.raises(ValidationError, match="access_token"):
        UpdateSharePointDataSourceRequest(
            **COMMON, auth_type=auth_type, full_reindex=True
        )


def test_sharepoint_oauth_update_without_reindex_needs_no_token():
    request = UpdateSharePointDataSourceRequest(**COMMON, auth_type="oauth_custom")
    assert request.access_token is None


def test_sharepoint_oauth_full_reindex_with_a_token_is_accepted():
    request = UpdateSharePointDataSourceRequest(
        **COMMON, auth_type="oauth_custom", full_reindex=True, access_token="tok"
    )
    assert request.access_token == "tok"


def test_sharepoint_full_reindex_with_integration_auth_needs_no_token():
    UpdateSharePointDataSourceRequest(
        **COMMON, auth_type="integration", full_reindex=True
    )


# --- SVN summary indexes carry a summarization model ----------------------------------


def test_svn_summary_create_sends_summarization_model():
    service = _service()
    service.create(
        SvnDataSourceRequest(
            **COMMON,
            link="svn://h/r",
            index_type="summary",
            summarization_model="gpt-4o",
        )
    )
    body = service._api.post.call_args.kwargs["json_data"]
    assert body["summarizationModel"] == "gpt-4o"
    assert body["indexType"] == "summary"


def test_svn_create_without_a_summarization_model_does_not_send_one():
    service = _service()
    service.create(SvnDataSourceRequest(**COMMON, link="svn://h/r", index_type="code"))
    assert "summarizationModel" not in service._api.post.call_args.kwargs["json_data"]
