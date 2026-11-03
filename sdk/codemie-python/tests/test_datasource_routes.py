from unittest.mock import MagicMock

import pytest

from codemie_sdk.models.datasource import (
    CodeDataSourceRequest,
    ConfluenceDataSourceRequest,
    BaseDataSourceRequest,
    DataSourceType,
    GitFaqDataSourceRequest,
    JiraDataSourceRequest,
    UpdateCodeDataSourceRequest,
    UpdateConfluenceDataSourceRequest,
    UpdateJiraDataSourceRequest,
    XWikiDataSourceRequest,
    UpdateXWikiDataSourceRequest,
)
from codemie_sdk.services.datasource import DatasourceService

COMMON = {"name": "my-ds", "project_name": "proj", "description": "d"}

# (request, expected create path) -- regression table for existing kinds plus
# the explicit route table.
CREATE_CASES = [
    (
        CodeDataSourceRequest(
            **COMMON,
            link="https://g/r",
            branch="main",
            embeddings_model="e",
            index_type="code",
        ),
        "/v1/application/proj/index",
    ),
    (
        JiraDataSourceRequest(**COMMON, jql="project = X"),
        "/v1/index/knowledge_base/jira",
    ),
    (
        ConfluenceDataSourceRequest(**COMMON, cql="space = X"),
        "/v1/index/knowledge_base/confluence",
    ),
    (XWikiDataSourceRequest(**COMMON, space="s"), "/v1/index/knowledge_base/xwiki"),
    (
        GitFaqDataSourceRequest(**COMMON, link="https://g/r", branch="main"),
        "/v1/index/knowledge_base/git_faq",
    ),
]

UPDATE_CASES = [
    (
        UpdateCodeDataSourceRequest(
            **COMMON,
            link="https://g/r",
            branch="main",
            embeddings_model="e",
            index_type="code",
        ),
        "/v1/application/proj/index/my-ds",
    ),
    (UpdateJiraDataSourceRequest(**COMMON, jql="p"), "/v1/index/knowledge_base/jira"),
    (
        UpdateConfluenceDataSourceRequest(**COMMON, cql="c"),
        "/v1/index/knowledge_base/confluence",
    ),
    (
        UpdateXWikiDataSourceRequest(**COMMON, space="s"),
        "/v1/index/knowledge_base/xwiki",
    ),
]


def _service():
    service = DatasourceService("http://x", "tok")
    service._api = MagicMock()
    return service


def test_svn_type_value():
    assert DataSourceType.SVN.value == "svn"


@pytest.mark.parametrize("request_obj,path", CREATE_CASES)
def test_create_routes(request_obj, path):
    service = _service()
    service.create(request_obj)
    assert service._api.post.call_args.args[0] == path


@pytest.mark.parametrize("request_obj,path", UPDATE_CASES)
def test_update_routes(request_obj, path):
    service = _service()
    service.update("id1", request_obj)
    assert service._api.put.call_args.args[0] == path


@pytest.mark.parametrize(
    "type_",
    [
        DataSourceType.PROVIDER,
        DataSourceType.SUMMARY,
        DataSourceType.JSON,
        DataSourceType.BEDROCK,
        DataSourceType.PLATFORM,
    ],
)
def test_types_without_route_raise_before_http(type_):
    service = _service()
    request = BaseDataSourceRequest(
        name="ds", project_name="p", description="d", type=type_
    )
    with pytest.raises(ValueError, match="Unsupported datasource type"):
        service.create(request)
    with pytest.raises(ValueError, match="Unsupported datasource type"):
        service.update("id1", request)
    service._api.post.assert_not_called()
    service._api.put.assert_not_called()
