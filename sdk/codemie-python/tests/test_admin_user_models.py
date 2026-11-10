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

"""Unit tests for the admin user list models, including budget assignments."""

from codemie_sdk.models.user import (
    AdminUserListItem,
    PaginatedUserListResponse,
    UserBudgetAssignmentInfo,
)


def _user_payload(**overrides):
    payload = {
        "id": "2bee0b02-53d2-4366-9f3a-d376357651a8",
        "username": "jane.doe",
        "email": "jane.doe@example.com",
        "name": "Jane Doe",
        "user_type": "regular",
        "is_active": True,
        "is_admin": False,
        "projects": [],
        "date": "2026-10-13T14:55:14.229513",
    }
    payload.update(overrides)
    return payload


def test_budget_assignments_are_deserialized():
    user = AdminUserListItem.model_validate(
        _user_payload(
            budget_assignments=[
                {
                    "category": "platform",
                    "budget_id": "default",
                    "budget_name": "Default",
                    "max_budget": 100.0,
                    "budget_duration": "30d",
                    "budget_reset_at": "2026-11-01T00:00:00Z",
                    "current_spending": 0.0223125,
                    "spend_unavailable": False,
                    "spend_partial": True,
                    "spend_missing_amount": 0.5,
                }
            ]
        )
    )

    assert len(user.budget_assignments) == 1
    assignment = user.budget_assignments[0]
    assert isinstance(assignment, UserBudgetAssignmentInfo)
    assert assignment.category == "platform"
    assert assignment.budget_id == "default"
    assert assignment.budget_name == "Default"
    assert assignment.max_budget == 100.0
    assert assignment.budget_duration == "30d"
    assert assignment.budget_reset_at == "2026-11-01T00:00:00Z"
    assert assignment.current_spending == 0.0223125
    assert assignment.spend_unavailable is False
    assert assignment.spend_partial is True
    assert assignment.spend_missing_amount == 0.5


def test_budget_assignment_without_a_spending_figure_keeps_it_unset():
    user = AdminUserListItem.model_validate(
        _user_payload(
            budget_assignments=[
                {
                    "category": "cli",
                    "budget_id": "cli-default",
                    "spend_unavailable": True,
                }
            ]
        )
    )

    assignment = user.budget_assignments[0]
    assert assignment.current_spending is None
    assert assignment.spend_unavailable is True
    assert assignment.spend_partial is False
    assert assignment.spend_missing_amount is None


def test_empty_budget_assignments_list_is_an_empty_list():
    user = AdminUserListItem.model_validate(_user_payload(budget_assignments=[]))

    assert user.budget_assignments == []


def test_missing_budget_assignments_key_defaults_to_an_empty_list():
    user = AdminUserListItem.model_validate(_user_payload())

    assert user.budget_assignments == []


def test_unknown_assignment_fields_are_ignored():
    assignment = UserBudgetAssignmentInfo.model_validate(
        {"category": "platform", "budget_id": "default", "added_later": "ignored"}
    )

    assert not hasattr(assignment, "added_later")


def test_paginated_response_carries_budget_assignments_per_user():
    response = PaginatedUserListResponse.model_validate(
        {
            "data": [
                _user_payload(
                    budget_assignments=[
                        {
                            "category": "premium_models",
                            "budget_id": "premium-default",
                            "current_spending": 1.25,
                        }
                    ]
                ),
                _user_payload(id="second-user", email="john.doe@example.com"),
            ],
            "pagination": {"total": 2, "page": 0, "per_page": 10},
        }
    )

    first, second = response.data
    assert first.budget_assignments[0].current_spending == 1.25
    assert second.budget_assignments == []
