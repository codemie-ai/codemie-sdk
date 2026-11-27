"""include_attachments / include_comments on Jira and Azure DevOps Work Item datasources.

The backend treats an omitted flag as "keep the stored value" on update and as the
default on create (off for Jira, the deployment setting for Work Items), so a flag the
caller did not set must not be sent at all.
"""

from unittest.mock import MagicMock

import pytest

from codemie_sdk.models.datasource import (
    AzureDevOpsWorkItem,
    AzureDevOpsWorkItemDataSourceRequest,
    Jira,
    JiraDataSourceRequest,
    UpdateAzureDevOpsWorkItemDataSourceRequest,
    UpdateJiraDataSourceRequest,
)
from codemie_sdk.services.datasource import DatasourceService

COMMON = {"name": "my-ds", "project_name": "proj", "description": "d"}
FLAGS = ("include_attachments", "include_comments")


def _service():
    service = DatasourceService("http://x", "tok")
    service._api = MagicMock()
    return service


def _create_body(request):
    service = _service()
    service.create(request)
    return service._api.post.call_args.kwargs["json_data"]


def _update_body(request):
    service = _service()
    service.update("id1", request)
    return service._api.put.call_args.kwargs["json_data"]


@pytest.mark.parametrize(
    "request_obj",
    [
        JiraDataSourceRequest(
            **COMMON,
            jql="project = X",
            include_attachments=True,
            include_comments=False,
        ),
        AzureDevOpsWorkItemDataSourceRequest(
            **COMMON, include_attachments=True, include_comments=False
        ),
    ],
)
def test_create_sends_flags_that_are_set(request_obj):
    body = _create_body(request_obj)

    assert body["include_attachments"] is True
    assert body["include_comments"] is False


@pytest.mark.parametrize(
    "request_obj",
    [
        JiraDataSourceRequest(**COMMON, jql="project = X"),
        AzureDevOpsWorkItemDataSourceRequest(**COMMON),
    ],
)
def test_create_omits_flags_that_are_not_set(request_obj):
    body = _create_body(request_obj)

    for flag in FLAGS:
        assert flag not in body


@pytest.mark.parametrize(
    "request_obj",
    [
        UpdateJiraDataSourceRequest(**COMMON, include_comments=False),
        UpdateAzureDevOpsWorkItemDataSourceRequest(**COMMON, include_comments=False),
    ],
)
def test_update_sends_only_the_flag_that_changes(request_obj):
    body = _update_body(request_obj)

    assert body["include_comments"] is False
    assert "include_attachments" not in body


@pytest.mark.parametrize(
    "request_obj",
    [
        UpdateJiraDataSourceRequest(**COMMON),
        UpdateAzureDevOpsWorkItemDataSourceRequest(**COMMON),
    ],
)
def test_update_without_flags_keeps_stored_values(request_obj):
    body = _update_body(request_obj)

    for flag in FLAGS:
        assert flag not in body


def test_response_exposes_stored_flags():
    """DataSource.jira / .azure_devops_work_item are parsed with these models."""
    jira = Jira.model_validate(
        {"jql": "project = X", "include_attachments": True, "include_comments": False}
    )
    work_item = AzureDevOpsWorkItem.model_validate(
        {"include_attachments": False, "include_comments": True}
    )

    assert (jira.include_attachments, jira.include_comments) == (True, False)
    assert (work_item.include_attachments, work_item.include_comments) == (False, True)
