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

"""Unit tests for the cost center budget rollup models."""

from codemie_sdk.models.cost_center import (
    CostCenterAssignedBudgetSummary,
    CostCenterBudgetSummary,
)


def _category_payload(**overrides):
    payload = {
        "budget_category": "platform",
        "budget_duration": "30d",
        "soft_budget": 50.0,
        "max_budget": 100.0,
        "member_count": 2,
        "allocated_member_budget_total": 100.0,
        "current_spending": 12.5,
    }
    payload.update(overrides)
    return payload


def test_rollup_with_spending_keeps_the_figures():
    summary = CostCenterBudgetSummary.model_validate(
        {
            "current_spending": 12.5,
            "budget_limit": 100.0,
            "total_percent": 12.5,
            "budgets": [_category_payload()],
        }
    )

    assert summary.current_spending == 12.5
    assert summary.total_percent == 12.5
    assert summary.spend_unavailable is False
    assert summary.spend_partial is False
    assert summary.spend_missing_amount is None
    assert summary.budgets[0].current_spending == 12.5


def test_rollup_without_a_spending_figure_parses_as_none():
    summary = CostCenterBudgetSummary.model_validate(
        {
            "current_spending": None,
            "budget_limit": None,
            "total_percent": None,
            "spend_unavailable": True,
            "budgets": [],
        }
    )

    assert summary.current_spending is None
    assert summary.total_percent is None
    assert summary.spend_unavailable is True
    assert summary.budgets == []


def test_rollup_spend_annotations_are_deserialized():
    summary = CostCenterBudgetSummary.model_validate(
        {
            "current_spending": 3.0,
            "total_percent": 3.0,
            "spend_partial": True,
            "spend_missing_amount": 0.75,
            "budgets": [],
        }
    )

    assert summary.spend_partial is True
    assert summary.spend_missing_amount == 0.75


def test_rollup_missing_spend_keys_default_to_unset():
    summary = CostCenterBudgetSummary.model_validate({"budgets": []})

    assert summary.current_spending is None
    assert summary.total_percent is None
    assert summary.spend_unavailable is False
    assert summary.spend_partial is False
    assert summary.spend_missing_amount is None


def test_category_without_a_spending_figure_parses_as_none():
    category = CostCenterAssignedBudgetSummary.model_validate(
        _category_payload(current_spending=None, spend_unavailable=True)
    )

    assert category.current_spending is None
    assert category.spend_unavailable is True
    assert category.spend_partial is False
    assert category.excluded_count == 0
    assert category.unsynced_count == 0


def test_category_spend_annotations_are_deserialized():
    category = CostCenterAssignedBudgetSummary.model_validate(
        _category_payload(spend_partial=True, spend_missing_amount=1.5)
    )

    assert category.current_spending == 12.5
    assert category.spend_partial is True
    assert category.spend_missing_amount == 1.5
