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

"""Project management service for the CodeMie SDK."""

from typing import Literal
from uuid import UUID

import requests

from ..models.project import (
    BulkAssignmentRequest,
    BulkAssignmentResponse,
    BulkAssignmentUserItem,
    CsvImportValidationResponse,
    PaginatedProjectListResponse,
    ProjectAllowedModelsResponse,
    ProjectAllowedModelsUpdateRequest,
    ProjectAssignmentRequest,
    ProjectAssignmentResponse,
    ProjectAssignmentUpdateRequest,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectDeleteResponse,
    ProjectDetailResponse,
    ProjectOwnershipUpdateRequest,
    ProjectOwnershipUpdateResponse,
    ProjectUpdateRequest,
    ProjectUpdateResponse,
    UserModelOverrideBatchRequest,
    UserModelOverrideRequest,
    UserModelOverrideResponse,
)
from ..utils.http import ApiRequestHandler, TokenSource


class ProjectService:
    """Service for managing projects in CodeMie."""

    def __init__(self, api_domain: str, token: TokenSource, verify_ssl: bool = True):
        """Initialize the ProjectService.

        Args:
            api_domain: Base URL for the CodeMie API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    @staticmethod
    def _cost_center_id(value: UUID | str) -> str:
        try:
            return str(UUID(str(value)))
        except ValueError:
            raise ValueError(
                f"cost_center_ids contains an invalid UUID: {value!r}"
            ) from None

    def create_project(
        self,
        name: str,
        description: str | None = None,
        cost_center_id: UUID | None = None,
        display_name: str | None = None,
        cli_analytics_enabled: bool | None = None,
    ) -> ProjectCreateResponse:
        """Create a new shared project.

        Args:
            name: Project name
            description: Project description (optional)
            cost_center_id: Optional cost center ID
            display_name: Human-friendly display name (max 150 chars)
            cli_analytics_enabled: Enable CLI analytics ingestion (None = not sent)

        Returns:
            ProjectCreateResponse with project details

        Raises:
            HTTPException: If project creation fails
        """
        payload = ProjectCreateRequest(
            name=name,
            description=description,
            cost_center_id=cost_center_id,
            display_name=display_name,
            cli_analytics_enabled=cli_analytics_enabled,
        )

        return self._api.post(
            "/v1/projects",
            response_model=ProjectCreateResponse,
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )

    def list_projects(
        self,
        search: str | None = None,
        page: int = 0,
        per_page: int = 20,
        include_counters: bool = True,
        include_budgets: bool = False,
        has_assigned_budgets: bool = False,
        sort_by: Literal["name", "created_at"] | None = None,
        sort_order: Literal["asc", "desc"] = "asc",
        cost_center_ids: list[UUID] | None = None,
    ) -> PaginatedProjectListResponse:
        """List projects visible to current user with pagination and search.

        Args:
            search: Search by project name or description (substring match)
            page: Page number (0-indexed)
            per_page: Items per page (10-100)
            include_budgets: Include compact assigned budget summaries for project rows
            has_assigned_budgets: Return only projects with at least one active
                assigned project budget
            sort_by: Sort field (name or created_at); ignored when search is active
            sort_order: Sort direction (asc or desc)
            cost_center_ids: Return only projects assigned to any of these cost centers;
                sent as one repeated query parameter per id, omitted when empty or None

        Returns:
            PaginatedProjectListResponse with projects and pagination info

        Raises:
            TypeError: If cost_center_ids is a single value instead of a list
            ValueError: If cost_center_ids contains an invalid UUID
        """
        params = {
            "page": page,
            "per_page": per_page,
            "include_counters": include_counters,
            "include_budgets": include_budgets,
            "has_assigned_budgets": has_assigned_budgets,
            "sort_order": sort_order,
        }

        if search is not None:
            params["search"] = search
        if sort_by is not None:
            params["sort_by"] = sort_by
        if cost_center_ids:
            if isinstance(cost_center_ids, (str, UUID)):
                raise TypeError(
                    "cost_center_ids must be a list of UUIDs, not a single value"
                )
            params["cost_center_ids"] = [
                self._cost_center_id(item) for item in cost_center_ids
            ]

        return self._api.get(
            "/v1/projects",
            response_model=PaginatedProjectListResponse,
            params=params,
            wrap_response=False,
        )

    def get_project_detail(
        self,
        project_name: str,
    ) -> ProjectDetailResponse:
        """Get project detail with member list.

        Args:
            project_name: Project name

        Returns:
            ProjectDetailResponse with project details and member list

        Raises:
            HTTPException: If project not found or user doesn't have access (404)
        """
        return self._api.get(
            f"/v1/projects/{project_name}",
            response_model=ProjectDetailResponse,
        )

    def project_exists(self, project_name: str) -> bool:
        """Check whether a project exists and is visible to the caller.

        Returns:
            True if the project is found; False means not found or not visible.

        Raises:
            requests.exceptions.HTTPError: For any HTTP error other than 404.
            requests.exceptions.ConnectionError: If the API is unreachable.
        """
        try:
            self.get_project_detail(project_name)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return False
            raise
        return True

    def update_project(
        self,
        project_name: str,
        name: str | None = None,
        description: str | None = None,
        clear_description: bool = False,
        cost_center_id: UUID | None = None,
        clear_cost_center: bool = False,
        enforce_member_spend_limits: bool | None = None,
        display_name: str | None = None,
        chargeback_attribution: str | None = None,
        cli_analytics_enabled: bool | None = None,
    ) -> ProjectUpdateResponse:
        """Update a project.

        Args:
            project_name: Current project name
            name: New project name (optional)
            description: New description (optional)
            clear_description: Set to True to remove the description (mutually
                exclusive with passing `description`)
            cost_center_id: New cost center ID (optional)
            clear_cost_center: Set to True to remove cost center
            enforce_member_spend_limits: Enable/disable per-member spend enforcement
            display_name: Human-friendly display name (max 150 chars)
            chargeback_attribution: Chargeback attribution mode ("project" or "cost_center")
            cli_analytics_enabled: Enable/disable CLI analytics ingestion (None = not sent)

        Returns:
            ProjectUpdateResponse with updated project details

        Raises:
            HTTPException: If project update fails, including a 422 when both
                `description` and `clear_description` are provided together
        """
        payload = ProjectUpdateRequest(
            name=name,
            description=description,
            clear_description=clear_description,
            cost_center_id=cost_center_id,
            clear_cost_center=clear_cost_center,
            enforce_member_spend_limits=enforce_member_spend_limits,
            display_name=display_name,
            chargeback_attribution=chargeback_attribution,
            cli_analytics_enabled=cli_analytics_enabled,
        )

        return self._api.patch(
            f"/v1/projects/{project_name}",
            response_model=ProjectUpdateResponse,
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )

    def update_allowed_models(
        self,
        project_name: str,
        allowed_models: list[str] | None = None,
        default_model: str | None = None,
    ) -> ProjectAllowedModelsResponse:
        """Change the models a project may use and the model it starts on.

        Args:
            project_name: Project name
            allowed_models: Models the project is limited to (optional); a value
                requires a default model, stored or passed
            default_model: New default model (optional); the stored one is kept
                when it is not passed

        Returns:
            ProjectAllowedModelsResponse with the stored model settings

        Raises:
            HTTPException: 400 when a model cannot be chosen, 403 without the
                project admin or maintainer role, 404 when the project is unknown
        """
        payload = ProjectAllowedModelsUpdateRequest(
            allowed_models=allowed_models, default_model=default_model
        )
        return self._api.patch(
            f"/v1/projects/{project_name}/allowed-models",
            response_model=ProjectAllowedModelsResponse,
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )

    def reset_allowed_models(self, project_name: str) -> ProjectAllowedModelsResponse:
        """Remove the project's model restriction and its default model.

        Args:
            project_name: Project name

        Returns:
            ProjectAllowedModelsResponse with both settings cleared

        Raises:
            HTTPException: 403 without the project admin or maintainer role,
                404 when the project is unknown
        """
        return self._api.delete(
            f"/v1/projects/{project_name}/allowed-models",
            response_model=ProjectAllowedModelsResponse,
        )

    def set_user_model_override(
        self,
        project_name: str,
        user_id: str,
        allowed_models: list[str],
        default_model: str | None = None,
    ) -> UserModelOverrideResponse:
        """Set (replace) the models one project member may use.

        Args:
            project_name: Project name
            user_id: ID of the project member
            allowed_models: Models the member is limited to, whatever the project allows
            default_model: Model the member starts on; must be one of allowed_models

        Returns:
            UserModelOverrideResponse with the stored override

        Raises:
            HTTPError: 400 when a model is unknown, disabled, blank, deprecated and not
                already held, or the default is not in allowed_models or the user is not a
                member; 404 when the project or user is unknown or the caller cannot write
                to the project; 501 when the feature is off
        """
        payload = UserModelOverrideRequest(
            allowed_models=allowed_models, default_model=default_model
        )
        return self._api.put(
            f"/v1/projects/{project_name}/user-model-overrides/{user_id}",
            response_model=UserModelOverrideResponse,
            json_data=payload.model_dump(mode="json", exclude_none=True),
        )

    def get_user_model_override(
        self, project_name: str, user_id: str
    ) -> UserModelOverrideResponse:
        """Get the model override of one project member.

        Args:
            project_name: Project name
            user_id: ID of the project member

        Returns:
            UserModelOverrideResponse with the stored override

        Raises:
            HTTPError: 404 when the member has no override or the caller cannot write
                to the project
        """
        return self._api.get(
            f"/v1/projects/{project_name}/user-model-overrides/{user_id}",
            response_model=UserModelOverrideResponse,
        )

    def list_user_model_overrides(
        self, project_name: str, skip: int = 0, limit: int = 100
    ) -> list[UserModelOverrideResponse]:
        """List the model overrides of a project.

        Args:
            project_name: Project name
            skip: Number of overrides to skip
            limit: Maximum number of overrides to return (1-500)

        Returns:
            List of UserModelOverrideResponse

        Raises:
            HTTPError: 404 when the project is unknown or the caller cannot write to it
        """
        return self._api.get(
            f"/v1/projects/{project_name}/user-model-overrides",
            response_model=list[UserModelOverrideResponse],
            params={"skip": skip, "limit": limit},
            wrap_response=False,
        )

    def delete_user_model_override(self, project_name: str, user_id: str) -> None:
        """Remove the model override of one project member.

        Args:
            project_name: Project name
            user_id: ID of the project member

        Raises:
            HTTPError: 404 when the member has no override or the caller cannot write
                to the project
        """
        self._api.delete(
            f"/v1/projects/{project_name}/user-model-overrides/{user_id}",
            response_model=dict,
        )

    def batch_user_model_overrides(
        self,
        project_name: str,
        operation: str,
        user_ids: list[str],
        allowed_models: list[str] | None = None,
        default_model: str | None = None,
    ) -> list[UserModelOverrideResponse]:
        """Grant or revoke the model override of several project members at once.

        The batch is atomic: when one user fails, no user is changed.

        Args:
            project_name: Project name
            operation: "grant" saves the same override for every user, "revoke" removes it;
                any other value is refused by the platform
            user_ids: IDs of the project members (1-500)
            allowed_models: Models to grant; required for "grant"
            default_model: Model the users start on; must be one of allowed_models

        Returns:
            List of UserModelOverrideResponse, one per user granted, or the removed
            overrides for "revoke"

        Raises:
            HTTPError: 400 when the batch fails ("Batch operation failed; no users updated")
                or the request is invalid; 404 when the project is unknown or the caller
                cannot write to it; 501 when the feature is off
        """
        payload = UserModelOverrideBatchRequest(
            operation=operation,
            user_ids=user_ids,
            allowed_models=allowed_models,
            default_model=default_model,
        )
        return self._api.post(
            f"/v1/projects/{project_name}/user-model-overrides/batch",
            response_model=list[UserModelOverrideResponse],
            json_data=payload.model_dump(mode="json", exclude_none=True),
            wrap_response=False,
        )

    def delete_project(self, project_name: str) -> ProjectDeleteResponse:
        """Hard-delete a project if it has no assigned resources.

        Args:
            project_name: Project name

        Returns:
            ProjectDeleteResponse with deletion confirmation

        Raises:
            HTTPException: If project has assigned resources (409) or is personal (403)
        """
        return self._api.delete(
            f"/v1/projects/{project_name}",
            response_model=ProjectDeleteResponse,
        )

    def transfer_ownership(
        self,
        project_name: str,
        user_id: str,
    ) -> ProjectOwnershipUpdateResponse:
        """Transfer ownership of a project to another active user.

        Args:
            project_name: Project name
            user_id: ID of the user who becomes the new owner

        Returns:
            ProjectOwnershipUpdateResponse with the project name, new owner id and message

        Raises:
            HTTPException: 404 if the project or the target user is not found, or the
                caller may not manage the project; 403 if the project is personal
        """
        payload = ProjectOwnershipUpdateRequest(user_id=user_id)

        return self._api.put(
            f"/v1/projects/{project_name}/ownership",
            response_model=ProjectOwnershipUpdateResponse,
            json_data=payload.model_dump(),
            wrap_response=False,
        )

    # Assignment endpoints

    def assign_user_to_project(
        self,
        project_name: str,
        user_id: str,
        is_project_admin: bool,
    ) -> ProjectAssignmentResponse:
        """Assign a user to a project.

        Args:
            project_name: Project name
            user_id: User ID to assign
            is_project_admin: Whether user should be project admin

        Returns:
            ProjectAssignmentResponse with assignment details

        Raises:
            HTTPException: If assignment fails
        """
        payload = ProjectAssignmentRequest(
            user_id=user_id,
            is_project_admin=is_project_admin,
        )

        return self._api.post(
            f"/v1/projects/{project_name}/assignment",
            response_model=ProjectAssignmentResponse,
            json_data=payload.model_dump(exclude_none=True),
        )

    def update_user_project_assignment(
        self,
        project_name: str,
        user_id: str,
        is_project_admin: bool,
    ) -> ProjectAssignmentResponse:
        """Update a user's project-admin flag.

        Args:
            project_name: Project name
            user_id: User ID to update
            is_project_admin: New project admin flag value

        Returns:
            ProjectAssignmentResponse with updated assignment

        Raises:
            HTTPException: If user is not assigned to project (404)
        """
        payload = ProjectAssignmentUpdateRequest(is_project_admin=is_project_admin)

        return self._api.put(
            f"/v1/projects/{project_name}/assignment/{user_id}",
            response_model=ProjectAssignmentResponse,
            json_data=payload.model_dump(exclude_none=True),
        )

    def remove_user_from_project(
        self,
        project_name: str,
        user_id: str,
    ) -> ProjectAssignmentResponse:
        """Remove a user from a project.

        Args:
            project_name: Project name
            user_id: User ID to remove

        Returns:
            ProjectAssignmentResponse with removal confirmation

        Raises:
            HTTPException: If user is not assigned to project (404)
        """
        return self._api.delete(
            f"/v1/projects/{project_name}/assignment/{user_id}",
            response_model=ProjectAssignmentResponse,
        )

    def bulk_assign_users_to_project(
        self,
        project_name: str,
        users: list[BulkAssignmentUserItem],
    ) -> BulkAssignmentResponse:
        """Bulk assign/upsert users to a project.

        Assigns new users and updates roles for existing members in a single
        atomic operation.

        Args:
            project_name: Project name
            users: List of BulkAssignmentUserItem with user_id and is_project_admin (1-1000)

        Returns:
            BulkAssignmentResponse with per-user results

        Raises:
            HTTPException: If bulk assignment fails
        """
        payload = BulkAssignmentRequest(users=users)

        return self._api.post(
            f"/v1/projects/{project_name}/assignments",
            response_model=BulkAssignmentResponse,
            json_data=payload.model_dump(),
        )

    def bulk_remove_users_from_project(
        self,
        project_name: str,
        user_ids: list[str],
    ) -> BulkAssignmentResponse:
        """Bulk remove users from a project.

        Args:
            project_name: Project name
            user_ids: List of user IDs to remove (1-100)

        Returns:
            BulkAssignmentResponse with per-user results

        Raises:
            HTTPException: If bulk removal fails
        """
        params = [("user_id", user_id) for user_id in user_ids]

        return self._api.delete(
            f"/v1/projects/{project_name}/assignments",
            response_model=BulkAssignmentResponse,
            params=params,
        )

    # CSV import endpoints

    def validate_users_from_csv(
        self,
        project_name: str,
        file_content: bytes,
        filename: str = "users.csv",
    ) -> CsvImportValidationResponse:
        """Dry-run validation of a CSV file for user import.

        Validates each row (email format, role, system user existence) without
        modifying any data.

        Args:
            project_name: Project name
            file_content: CSV file content as bytes
            filename: CSV filename

        Returns:
            CsvImportValidationResponse with per-row validation results

        Raises:
            HTTPException: If file too large (413) or structural CSV error (422)
        """
        files = {"file": (filename, file_content, "text/csv")}

        return self._api.post_multipart(
            f"/v1/projects/{project_name}/import-users/validate",
            response_model=CsvImportValidationResponse,
            files=files,
        )

    def import_users_from_csv(
        self,
        project_name: str,
        file_content: bytes,
        filename: str = "users.csv",
    ) -> BulkAssignmentResponse:
        """Assign users to a project from a CSV file upload.

        CSV must include a header row with 'email' and 'role' columns.
        Allowed roles: 'administrator' (project admin), 'user' (regular member).

        Args:
            project_name: Project name
            file_content: CSV file content as bytes
            filename: CSV filename

        Returns:
            BulkAssignmentResponse with per-user results

        Raises:
            HTTPException: If file too large (413) or validation fails (422)
        """
        files = {"file": (filename, file_content, "text/csv")}

        return self._api.post_multipart(
            f"/v1/projects/{project_name}/import-users",
            response_model=BulkAssignmentResponse,
            files=files,
        )
