/** Models for user service. */

/** User API response. */
export interface AboutUserResponse {
  user_id: string;
  name: string;
  username: string;
  email: string;
  is_admin: boolean;
  applications: string[];
  applications_admin: string[];
  picture: string;
  knowledge_bases: string[];
}

/** User model. */
export interface AboutUser {
  user_id: string;
  name: string;
  username: string;
  email: string;
  is_admin: boolean;
  applications: string[];
  applications_admin: string[];
  picture: string;
  knowledge_bases: string[];
}

/** User data and preferences model. */
export interface UserData {
  id?: string;
  date?: string;
  update_date?: string;
  user_id?: string;
}

/** Project membership as shown in admin user lists. */
export interface AdminUserProjectInfo {
  name: string;
  display_name?: string | null;
  is_project_admin: boolean;
  is_default: boolean;
}

/** Budget assignment of a user, including spend status. */
export interface UserBudgetAssignmentInfo {
  category: string;
  budget_id: string;
  budget_name?: string | null;
  max_budget?: number | null;
  budget_duration?: string | null;
  budget_reset_at?: string | null;
  current_spending?: number | null;
  spend_unavailable: boolean;
  spend_partial: boolean;
  spend_missing_amount?: number | null;
}

/** Row of the admin user list. */
export interface AdminUserListItem {
  id: string;
  username: string;
  email: string;
  name?: string | null;
  user_type?: string | null;
  is_active: boolean;
  is_admin: boolean;
  is_maintainer: boolean;
  auth_source?: string | null;
  last_login_at?: string | null;
  projects: AdminUserProjectInfo[];
  budget_assignments: UserBudgetAssignmentInfo[];
  date?: string | null;
}

/** Page of admin users. */
export interface PaginatedAdminUserList {
  data: AdminUserListItem[];
  pagination: { total: number; page: number; per_page: number };
}

/** Full admin view of a user. */
export interface CodeMieUserDetail {
  id: string;
  username: string;
  email: string;
  name?: string | null;
  picture?: string | null;
  user_type?: string | null;
  is_active: boolean;
  is_admin: boolean;
  is_maintainer: boolean;
  auth_source?: string | null;
  email_verified: boolean;
  last_login_at?: string | null;
  projects: AdminUserProjectInfo[];
  project_limit?: number | null;
  knowledge_bases: string[];
  date?: string | null;
  update_date?: string | null;
  deleted_at?: string | null;
}

/** Fields an admin may change on a user. */
export interface AdminUserUpdate {
  name?: string | null;
  picture?: string | null;
  is_admin?: boolean;
  is_maintainer?: boolean;
  /** Only `false` is accepted here; use reactivateUser to set a user active again. */
  is_active?: boolean;
  project_limit?: number | null;
}

/** A user's membership in one project. */
export interface AdminUserProject {
  project_name: string;
  is_project_admin: boolean;
  is_default: boolean;
  date?: string | null;
}
