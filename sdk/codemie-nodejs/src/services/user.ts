import { UserMapper } from "../mappers/user.mapper";
import type { AuthConfig } from "../models/common";
import type {
  AboutUser,
  AboutUserResponse,
  AdminUserProject,
  AdminUserUpdate,
  CodeMieUserDetail,
  PaginatedAdminUserList,
  UserData,
} from "../models/user";
import { ApiRequestHandler } from "../utils/http";

export class UserService {
  private api: ApiRequestHandler;

  constructor(config: AuthConfig) {
    this.api = new ApiRequestHandler(config);
  }

  /**
   * Get current user profile.
   */
  async aboutMe(): Promise<AboutUser> {
    const response = await this.api.get<AboutUserResponse>("/v1/user");
    return UserMapper.mapAboutUserResponse(response);
  }

  /**
   * Get user data and preferences.
   */
  async getData(): Promise<UserData> {
    return this.api.get("/v1/user/data");
  }

  private adminPath(id: string, ...rest: string[]): string {
    if (!id) throw new Error("user id must not be empty");
    return ["/v1/admin/users", encodeURIComponent(id), ...rest].join("/");
  }

  private memberPath(userId: string, projectName: string, ...rest: string[]): string {
    if (!projectName) throw new Error("projectName must not be empty");
    return this.adminPath(userId, "projects", encodeURIComponent(projectName), ...rest);
  }

  /**
   * List users (admin only). `filters` is a JSON string.
   */
  async listAdminUsers(
    page = 0,
    perPage = 20,
    search?: string,
    filters?: string
  ): Promise<PaginatedAdminUserList> {
    const params: Record<string, unknown> = { page, per_page: perPage };
    if (search) params.search = search;
    if (filters) params.filters = filters;
    return this.api.get("/v1/admin/users", params);
  }

  /** Get a user's admin details. */
  async getAdminUser(id: string): Promise<CodeMieUserDetail> {
    return this.api.get(this.adminPath(id));
  }

  /** Update a user's admin-editable fields. */
  async updateAdminUser(id: string, fields: AdminUserUpdate): Promise<CodeMieUserDetail> {
    return this.api.put(this.adminPath(id), fields);
  }

  /** Get a user's project memberships. */
  async getUserProjects(id: string): Promise<AdminUserProject[]> {
    const response = await this.api.get<{ projects: AdminUserProject[] }>(
      this.adminPath(id, "projects")
    );
    return response.projects;
  }

  /**
   * Add a user to a project.
   * Argument order is (userId, projectName); the same-named ProjectService
   * methods take (projectName, userId).
   */
  async assignUserToProject(
    userId: string,
    projectName: string,
    isProjectAdmin = false
  ): Promise<Record<string, unknown>> {
    return this.api.post(this.adminPath(userId, "projects"), {
      project_name: projectName,
      is_project_admin: isProjectAdmin,
    });
  }

  /**
   * Remove a user from a project.
   * Argument order is (userId, projectName); ProjectService takes (projectName, userId).
   */
  async removeUserFromProject(userId: string, projectName: string): Promise<void> {
    await this.api.delete(this.memberPath(userId, projectName));
  }

  /**
   * Change a user's role in a project.
   * Argument order is (userId, projectName); ProjectService takes (projectName, userId).
   */
  async updateUserProjectRole(
    userId: string,
    projectName: string,
    isProjectAdmin: boolean
  ): Promise<void> {
    await this.api.put(this.memberPath(userId, projectName), {
      is_project_admin: isProjectAdmin,
    });
  }

  /**
   * Make a project the user's default.
   * Argument order is (userId, projectName); ProjectService takes (projectName, userId).
   */
  async setDefaultProject(userId: string, projectName: string): Promise<Record<string, unknown>> {
    return this.api.put(this.memberPath(userId, projectName, "default"), {});
  }

  /**
   * Clear the user's default project.
   * Argument order is (userId, projectName); ProjectService takes (projectName, userId).
   */
  async clearDefaultProject(userId: string, projectName: string): Promise<Record<string, unknown>> {
    return this.api.delete(this.memberPath(userId, projectName, "default"));
  }

  /** Deactivate a user. */
  async deactivateUser(id: string): Promise<void> {
    await this.api.delete(this.adminPath(id));
  }

  /** Reactivate a user. Has its own endpoint: updating with is_active=true is refused by the API. */
  async reactivateUser(id: string): Promise<CodeMieUserDetail> {
    return this.api.post(this.adminPath(id, "reactivate"));
  }
}
