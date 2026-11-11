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

"""Provisioning API models for the CodeMie SDK.

The provisioning routes are callable only by registered provisioning clients. The request
models are deliberately permissive: the server owns the validation rules, so the SDK sends
what the caller gives it (including unknown fields) and surfaces the server's verdict as
an HTTP error.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProvisioningProject(BaseModel):
    """A shared project returned by the project lookup."""

    model_config = ConfigDict(extra="ignore")

    project_name: str
    display_name: str | None = None


class ProvisioningProjectBlock(BaseModel):
    """Project settings applied together with a budget.

    Attributes:
        cost_center: Cost center to link the project to while it has no active one.
        admin_emails: People to make project admins; existing admins are never removed.
    """

    model_config = ConfigDict(extra="allow")

    cost_center: str | None = None
    admin_emails: list[str] | None = None


class ProvisioningBudgetRequest(BaseModel):
    """Request body for setting or adjusting a project budget.

    Attributes:
        amounts: Monthly budget in USD per category (``platform``, ``cli``,
            ``premium_models``).
        project: Optional project settings. An empty block is sent as ``{}``; ``None``
            leaves the block out of the body.
    """

    # Non-finite amounts are sent as the JSON constants NaN / Infinity instead of null,
    # so the server, not the client, rejects them.
    model_config = ConfigDict(extra="allow", ser_json_inf_nan="constants")

    amounts: dict[str, float]
    project: ProvisioningProjectBlock | None = None


class ProvisioningBudgetCategory(BaseModel):
    """Budget of one spend category in a budget response."""

    model_config = ConfigDict(extra="ignore")

    category: str
    max_budget: float
    soft_budget: float
    budget_reset_at: str | None = None


class ProvisioningBudgetGroup(BaseModel):
    """Budget of a project after the call."""

    model_config = ConfigDict(extra="ignore")

    total_amount: float
    budget_duration: str
    categories: list[ProvisioningBudgetCategory]


class ProvisioningBudgetResponse(BaseModel):
    """Outcome of a set or adjust call.

    ``budget`` is always present: the API never answers a set or adjust with a null budget.
    A cancel answers 204 without a body, which :class:`ProvisioningBudgetResult` represents
    with ``budget=None``.
    """

    model_config = ConfigDict(extra="ignore")

    project_name: str
    cost_center: str | None = None
    created_project: bool
    created_cost_center: bool
    created_budget: bool
    budget: ProvisioningBudgetGroup
    admins_assigned: list[str] = Field(default_factory=list)
    admins_not_assigned: list[str] = Field(default_factory=list)


class ProvisioningBudgetResult(BaseModel):
    """A budget call's HTTP status together with its parsed body.

    The status is part of the contract (201 when the call created the budget, 200 when it
    replaced or adjusted one, 204 after a cancel), so it is returned rather than hidden.

    Attributes:
        status_code: HTTP status of the successful answer.
        budget: Parsed body, or ``None`` when the answer has no body (cancel).
    """

    model_config = ConfigDict(extra="ignore")

    status_code: int
    budget: ProvisioningBudgetResponse | None = None
