import FormData from "form-data";
import { z } from "zod";
import { NotFoundError } from "../exceptions";
import type { AuthConfig } from "../models/common";
import type {
  BulkAssignmentResponse,
  BulkAssignmentUserItem,
  CsvImportValidationResponse,
  ListProjectsOptions,
  PaginatedProjectList,
  ProjectAssignmentResponse,
  ProjectCreateRequest,
  ProjectCreateResponse,
  ProjectDeleteResponse,
  ProjectDetail,
  ProjectOwnershipUpdateResponse,
  ProjectUpdateRequest,
  ProjectUpdateResponse,
} from "../models/project";
import { ApiRequestHandler } from "../utils/http";

const bulkAssignSchema = z
  .array(z.object({ user_id: z.string(), is_project_admin: z.boolean() }))
  .min(1)
  .max(1000);
const bulkRemoveSchema = z.array(z.string()).min(1).max(100);

/** Unwrap the `data` envelope, falling back to the body when absent. */
function unwrap<T>(body: unknown): T {
  if (body && typeof body === "object" && "data" in body) {
    return (body as { data: T }).data;
  }
  return body as T;
}

const enc = (v: string): string => {
  if (!v) throw new Error("path id must not be empty");
  return encodeURIComponent(v);
};
const flag = (value: boolean) => (value ? "True" : "False");

export class ProjectService {
  private api: ApiRequestHandler;

  constructor(config: AuthConfig) {
    this.api = new ApiRequestHandler(config);
  }

  /** POST /v1/projects */
  async createProject(request: ProjectCreateRequest): Promise<ProjectCreateResponse> {
    return unwrap(await this.api.post<unknown>("/v1/projects", request));
  }

  /** GET /v1/projects (raw body, no envelope) */
  async listProjects(options: ListProjectsOptions = {}): Promise<PaginatedProjectList> {
    const params: Record<string, unknown> = {
      page: options.page ?? 0,
      per_page: options.per_page ?? 20,
      include_counters: flag(options.include_counters ?? true),
      include_budgets: flag(options.include_budgets ?? false),
      has_assigned_budgets: flag(options.has_assigned_budgets ?? false),
      sort_order: options.sort_order ?? "asc",
    };
    if (options.search !== undefined) params.search = options.search;
    if (options.sort_by !== undefined) params.sort_by = options.sort_by;

    return this.api.get<PaginatedProjectList>("/v1/projects", params);
  }

  /** GET /v1/projects/{name} */
  async getProjectDetail(projectName: string): Promise<ProjectDetail> {
    return unwrap(await this.api.get<unknown>(`/v1/projects/${enc(projectName)}`));
  }

  /** PATCH /v1/projects/{name}; the clear_* flags are always sent. */
  async updateProject(
    projectName: string,
    request: ProjectUpdateRequest,
  ): Promise<ProjectUpdateResponse> {
    const defined = Object.fromEntries(
      Object.entries(request).filter(([, value]) => value !== undefined),
    );
    const payload = { clear_description: false, clear_cost_center: false, ...defined };
    return unwrap(await this.api.patch<unknown>(`/v1/projects/${enc(projectName)}`, payload));
  }

  /** DELETE /v1/projects/{name} */
  async deleteProject(projectName: string): Promise<ProjectDeleteResponse> {
    return unwrap(await this.api.delete<unknown>(`/v1/projects/${enc(projectName)}`));
  }

  /** PUT /v1/projects/{name}/ownership (raw body, no envelope) */
  async transferOwnership(
    projectName: string,
    userId: string,
  ): Promise<ProjectOwnershipUpdateResponse> {
    return this.api.put<ProjectOwnershipUpdateResponse>(
      `/v1/projects/${enc(projectName)}/ownership`,
      { user_id: userId },
    );
  }

  /** POST /v1/projects/{name}/assignment */
  async assignUserToProject(
    projectName: string,
    userId: string,
    isProjectAdmin = false,
  ): Promise<ProjectAssignmentResponse> {
    return unwrap(
      await this.api.post<unknown>(`/v1/projects/${enc(projectName)}/assignment`, {
        user_id: userId,
        is_project_admin: isProjectAdmin,
      }),
    );
  }

  /** PUT /v1/projects/{name}/assignment/{user_id} */
  async updateUserProjectAssignment(
    projectName: string,
    userId: string,
    isProjectAdmin: boolean,
  ): Promise<ProjectAssignmentResponse> {
    return unwrap(
      await this.api.put<unknown>(`/v1/projects/${enc(projectName)}/assignment/${enc(userId)}`, {
        is_project_admin: isProjectAdmin,
      }),
    );
  }

  /** DELETE /v1/projects/{name}/assignment/{user_id} */
  async removeUserFromProject(
    projectName: string,
    userId: string,
  ): Promise<ProjectAssignmentResponse> {
    return unwrap(
      await this.api.delete<unknown>(`/v1/projects/${enc(projectName)}/assignment/${enc(userId)}`),
    );
  }

  /** POST /v1/projects/{name}/assignments (1-1000 users) */
  async bulkAssignUsersToProject(
    projectName: string,
    users: BulkAssignmentUserItem[],
  ): Promise<BulkAssignmentResponse> {
    bulkAssignSchema.parse(users);
    return unwrap(
      await this.api.post<unknown>(`/v1/projects/${enc(projectName)}/assignments`, { users }),
    );
  }

  /** DELETE /v1/projects/{name}/assignments?user_id=a&user_id=b (1-100 ids) */
  async bulkRemoveUsersFromProject(
    projectName: string,
    userIds: string[],
  ): Promise<BulkAssignmentResponse> {
    bulkRemoveSchema.parse(userIds);
    return unwrap(
      await this.api.delete<unknown>(`/v1/projects/${enc(projectName)}/assignments`, {
        params: { user_id: userIds },
        paramsSerializer: (params: { user_id: string[] }) => {
          const query = new URLSearchParams();
          for (const id of params.user_id) query.append("user_id", id);
          return query.toString();
        },
      }),
    );
  }

  /** POST /v1/projects/{name}/import-users/validate */
  async validateUsersFromCsv(
    projectName: string,
    csv: Buffer,
    filename = "users.csv",
  ): Promise<CsvImportValidationResponse> {
    return unwrap(
      await this.api.postMultipart<unknown>(
        `/v1/projects/${enc(projectName)}/import-users/validate`,
        this.csvForm(csv, filename),
      ),
    );
  }

  /** POST /v1/projects/{name}/import-users */
  async importUsersFromCsv(
    projectName: string,
    csv: Buffer,
    filename = "users.csv",
  ): Promise<BulkAssignmentResponse> {
    return unwrap(
      await this.api.postMultipart<unknown>(
        `/v1/projects/${enc(projectName)}/import-users`,
        this.csvForm(csv, filename),
      ),
    );
  }

  /**
   * True when the project is visible to the caller. The backend answers 404
   * for both missing and not-visible projects; other errors are rethrown.
   */
  async projectExists(projectName: string): Promise<boolean> {
    try {
      await this.getProjectDetail(projectName);
      return true;
    } catch (error) {
      if (error instanceof NotFoundError) return false;
      throw error;
    }
  }

  private csvForm(csv: Buffer, filename: string): FormData {
    const formData = new FormData();
    formData.append("file", csv, { filename, contentType: "text/csv" });
    return formData;
  }
}
