// Copyright 2026 EPAM Systems, Inc. ("EPAM")
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

export interface ProjectCounters {
  assistants_count: number;
  workflows_count: number;
  integrations_count: number;
  datasources_count: number;
  skills_count: number;
}

export interface ProjectMember {
  user_id: string;
  is_project_admin: boolean;
  date?: string | null;
}

export interface ProjectBudgetItem {
  budget_id: string;
  name: string;
  budget_category: string;
  soft_budget: number;
  max_budget: number;
  budget_duration: string;
  budget_reset_at?: string | null;
  provider_sync_status?: string | null;
  member_count: number;
  allocated_member_budget_total: number;
  current_spending?: number | null;
}

export interface ProjectListItem {
  name: string;
  display_name?: string | null;
  description?: string | null;
  project_type: string;
  created_by?: string | null;
  user_count: number;
  admin_count: number;
  created_at?: string | null;
  counters?: ProjectCounters | null;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  spending?: number | null;
  current_spending?: number | null;
  budgets?: ProjectBudgetItem[] | null;
  chargeback_enabled?: boolean;
  chargeback_attribution?: string;
  cli_analytics_enabled?: boolean | null;
}

export interface ProjectPaginationInfo {
  total: number;
  page: number;
  per_page: number;
}

export interface PaginatedProjectList {
  data: ProjectListItem[];
  pagination: ProjectPaginationInfo;
}

export interface ProjectDetail {
  name: string;
  display_name?: string | null;
  description?: string | null;
  project_type: string;
  created_by?: string | null;
  user_count: number;
  admin_count: number;
  created_at?: string | null;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  members: ProjectMember[];
  enforce_member_spend_limits?: boolean;
  chargeback_enabled?: boolean;
  allowed_models?: string[] | null;
  default_model?: string | null;
  chargeback_attribution?: string;
  cli_analytics_enabled?: boolean | null;
}

export interface ProjectCreateRequest {
  name: string;
  /** Max 150 characters. */
  display_name?: string;
  description?: string;
  cost_center_id?: string;
  cli_analytics_enabled?: boolean;
}

export interface ProjectCreateResponse {
  name: string;
  display_name?: string | null;
  description?: string | null;
  project_type: string;
  created_by: string;
  created_at: string;
  cost_center_id?: string | null;
  cost_center_name?: string | null;
  enforce_member_spend_limits?: boolean;
  chargeback_attribution?: string;
  cli_analytics_enabled?: boolean | null;
}

export type ProjectUpdateResponse = ProjectCreateResponse;

export interface ProjectUpdateRequest {
  name?: string;
  /** Max 150 characters. */
  display_name?: string;
  description?: string;
  clear_description?: boolean;
  cost_center_id?: string;
  clear_cost_center?: boolean;
  enforce_member_spend_limits?: boolean;
  chargeback_attribution?: string;
  cli_analytics_enabled?: boolean;
}

export interface ProjectOwnershipUpdateResponse {
  name: string;
  created_by: string;
  message: string;
}

export interface ProjectDeleteResponse {
  message: string;
  name: string;
}

export interface ProjectAssignmentResponse {
  message: string;
  user_id: string;
  project_name: string;
  is_project_admin?: boolean | null;
}

export interface BulkAssignmentUserItem {
  user_id: string;
  is_project_admin: boolean;
}

export interface BulkAssignmentResultItem {
  user_id: string;
  action: "assigned" | "updated" | "removed";
  is_project_admin?: boolean | null;
}

export interface BulkAssignmentResponse {
  message: string;
  project_name: string;
  total: number;
  results: BulkAssignmentResultItem[];
}

export interface CsvImportRowResult {
  email: string;
  role: string;
  error?: string | null;
}

export interface CsvImportValidationResponse {
  users: CsvImportRowResult[];
}

export interface ListProjectsOptions {
  search?: string;
  page?: number;
  per_page?: number;
  include_counters?: boolean;
  include_budgets?: boolean;
  has_assigned_budgets?: boolean;
  sort_by?: "name" | "created_at";
  sort_order?: "asc" | "desc";
}
