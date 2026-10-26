import { WorkflowMapper } from "../mappers/workflow.mapper";
import type { AnyJson, PaginatedResponse, AuthConfig } from "../models/common";
import type {
  Workflow,
  WorkflowResponse,
  WorkflowVersionHistoryResponse,
} from "../models/workflow";
import {
  WorkflowCreateParamsSchema,
  type WorkflowCreateParams,
  WorkflowEvaluationParamsSchema,
  type WorkflowEvaluationParams,
  WorkflowListParamsSchema,
  type WorkflowListParams,
  WorkflowRollbackParamsSchema,
  WorkflowUpdateParamsSchema,
  type WorkflowUpdateParams,
} from "../schemas/workflow";
import { ApiRequestHandler } from "../utils/http";
import { WorkflowExecutionService } from "./workflow_execution";

export class WorkflowService {
  private api: ApiRequestHandler;

  constructor(config: AuthConfig) {
    this.api = new ApiRequestHandler(config);
  }

  /**
   * Get list of prebuilt workflows.
   */
  async getPrebuilt(): Promise<Workflow[]> {
    const response = await this.api.get<WorkflowResponse[]>("/v1/workflows/prebuilt");
    const prebuiltItems = Array.isArray(response) ? response : [];
    return prebuiltItems.map(WorkflowMapper.mapWorkflowResponse);
  }

  /**
   * Create a new workflow.
   */
  async create(_params: WorkflowCreateParams): Promise<AnyJson> {
    const params = WorkflowCreateParamsSchema.parse(_params);
    return this.api.post("/v1/workflows", params);
  }

  /**
   * Update an existing workflow.
   */
  async update(workflowId: string, _params: WorkflowUpdateParams): Promise<AnyJson> {
    const params = WorkflowUpdateParamsSchema.parse(_params);
    return this.api.put(`/v1/workflows/${workflowId}`, params);
  }

  /**
   * List workflows with filtering and pagination support.
   */
  async list(_params: WorkflowListParams = {}): Promise<Workflow[]> {
    const params = WorkflowListParamsSchema.parse(_params);

    const queryParams: Record<string, number | string> = {
      page: params.page,
      per_page: params.per_page,
    };

    const filters: Record<string, string | string[]> = {};
    if (params.projects?.length) filters.project = params.projects;
    if (params.search) filters.name = params.search;
    if (Object.keys(filters).length)
      queryParams.filters = JSON.stringify(filters);

    const workflows = await this.api.get<PaginatedResponse<WorkflowResponse>>(
      "/v1/workflows",
      queryParams,
    );

    const items = Array.isArray(workflows?.data) ? workflows.data : [];
    return items.map(WorkflowMapper.mapWorkflowResponse);
  }

  /**
   * Get workflow by ID.
   */
  async get(workflowId: string): Promise<Workflow> {
    const response = await this.api.get<WorkflowResponse>(`/v1/workflows/id/${workflowId}`);
    return WorkflowMapper.mapWorkflowResponse(response);
  }

  /**
   * Delete a workflow by ID.
   */
  async delete(workflowId: string): Promise<AnyJson> {
    return this.api.delete(`/v1/workflows/${workflowId}`);
  }

  /**
   * Run a workflow by ID.
   */
  async run(
    workflowId: string,
    userInput?: string | Record<string, unknown> | unknown[] | number | boolean,
    fileName?: string,
    sessionId?: string,
    propagateHeaders?: boolean,
    headers?: Record<string, string>,
    tags?: string[],
  ): Promise<AnyJson> {
    return this.executions(workflowId).create(
      userInput,
      fileName,
      sessionId,
      propagateHeaders,
      headers,
      tags,
    );
  }

  /**
   * Evaluate a workflow with a dataset.
   */
  async evaluate(workflowId: string, _params: WorkflowEvaluationParams): Promise<AnyJson> {
    const params = WorkflowEvaluationParamsSchema.parse(_params);
    return this.api.post(`/v1/workflows/${workflowId}/evaluate`, params);
  }

  /**
   * Get revision history for a workflow.
   */
  async listVersions(workflowId: string): Promise<WorkflowVersionHistoryResponse> {
    return this.api.get<WorkflowVersionHistoryResponse>(`/v1/workflows/${workflowId}/versions`);
  }

  /**
   * Roll the workflow back to a prior revision by positional index.
   * revision_index is 0-based into the revisions[] array returned by listVersions.
   */
  async rollback(
    workflowId: string,
    revisionIndex: number,
    changeNotes?: string,
  ): Promise<{ message: string }> {
    const params = WorkflowRollbackParamsSchema.parse({
      revision_index: revisionIndex,
      ...(changeNotes !== undefined ? { change_notes: changeNotes } : {}),
    });
    return this.api.post<{ message: string }>(
      `/v1/workflows/${workflowId}/versions/rollback`,
      params,
    );
  }

  /**
   * Get workflow execution service for the specified workflow.
   */
  executions(workflowId: string): WorkflowExecutionService {
    return new WorkflowExecutionService(this.api, workflowId);
  }
}
