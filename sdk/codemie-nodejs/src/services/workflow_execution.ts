import { WorkflowMapper } from "../mappers/workflow.mapper";
import type { AnyJson, PaginatedResponse } from "../models/common";
import type { WorkflowExecution, WorkflowExecutionResponse } from "../models/workflow";
import {
  WorkflowExecutionCreateParamsSchema,
  WorkflowExecutionListParamsSchema,
  type WorkflowExecutionListParams,
} from "../schemas/workflow";
import type { ApiRequestHandler } from "../utils/http";
import { WorkflowExecutionStateService } from "./workflow_execution_state";

export class WorkflowExecutionService {
  private api: ApiRequestHandler;
  private workflowId: string;

  constructor(api: ApiRequestHandler, workflowId: string) {
    this.api = api;
    this.workflowId = workflowId;
  }

  /**
   * List executions for the workflow with filtering and pagination support.
   */
  async list(_params: WorkflowExecutionListParams = {}): Promise<WorkflowExecution[]> {
    const params = WorkflowExecutionListParamsSchema.parse(_params);

    const queryParams = {
      page: params.page,
      per_page: params.per_page,
    };

    const response = await this.api.get<PaginatedResponse<WorkflowExecutionResponse>>(
      `/v1/workflows/${this.workflowId}/executions`,
      queryParams,
    );

    return response.data.map(WorkflowMapper.mapWorkflowExecutionResponse);
  }

  /**
   * Create a new workflow execution.
   */
  async create(
    userInput?: string | Record<string, unknown> | unknown[] | number | boolean,
    fileName?: string,
    sessionId?: string,
    propagateHeaders?: boolean,
    headers?: Record<string, string>,
    tags?: string[],
    attributes?: Record<string, string>,
  ): Promise<AnyJson> {
    const params = WorkflowExecutionCreateParamsSchema.parse({
      user_input: userInput,
      file_name: fileName,
      session_id: sessionId,
      propagate_headers: propagateHeaders,
      tags,
      attributes,
    });
    return this.api.post(`/v1/workflows/${this.workflowId}/executions`, params, {}, headers);
  }

  /**
   * Get workflow execution by ID.
   */
  async get(executionId: string): Promise<WorkflowExecution> {
    const response = await this.api.get<WorkflowExecutionResponse>(
      `/v1/workflows/${this.workflowId}/executions/${executionId}`,
    );
    return WorkflowMapper.mapWorkflowExecutionResponse(response);
  }

  /**
   * Get states service for a specific workflow execution.
   */
  states(executionId: string): WorkflowExecutionStateService {
    return new WorkflowExecutionStateService(this.api, this.workflowId, executionId);
  }

  /**
   * Delete all workflow executions.
   */
  async deleteAll(): Promise<AnyJson> {
    return this.api.delete(`/v1/workflows/${this.workflowId}/executions`);
  }

  /**
   * Abort a running workflow execution.
   */
  async abort(executionId: string): Promise<AnyJson> {
    return this.api.put(`/v1/workflows/${this.workflowId}/executions/${executionId}/abort`);
  }

  /**
   * Resume an interrupted workflow execution.
   */
  async resume(
    executionId: string,
    propagateHeaders?: boolean,
    headers?: Record<string, string>,
  ): Promise<AnyJson> {
    const config = { params: { propagate_headers: propagateHeaders } };
    // empty body per API; send {} with query param and optional headers
    return this.api.put(
      `/v1/workflows/${this.workflowId}/executions/${executionId}/resume`,
      {},
      config,
      headers,
    );
  }
}
