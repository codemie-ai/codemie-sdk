import type { AuthConfig } from "../models/common";
import type { SummariesResponse, TabularResponse, UsersListResponse } from "../models/analytics";
import {
  AnalyticsQueryParamsSchema,
  AssistantsRequestsQueryParamsSchema,
  AttributesAnalyticsQueryParamsSchema,
  AttributesUsageQueryParamsSchema,
  PaginatedAnalyticsQueryParamsSchema,
  type AnalyticsQueryParams,
  type AssistantsRequestsQueryParams,
  type AttributesAnalyticsQueryParams,
  type AttributesUsageQueryParams,
  type PaginatedAnalyticsQueryParams,
} from "../schemas/analytics";
import { ApiRequestHandler } from "../utils/http";

/**
 * Axios would serialize an object as `attributes[team]=alpha`; the backend expects a JSON string.
 * Returns the params with `attributes` JSON-encoded, or without the key when it is absent.
 */
function toQueryParams<T extends { attributes?: Record<string, string> }>(
  params: T,
): Omit<T, "attributes"> & { attributes?: string } {
  const { attributes, ...rest } = params;
  return attributes === undefined ? rest : { ...rest, attributes: JSON.stringify(attributes) };
}

export class AnalyticsService {
  private api: ApiRequestHandler;

  constructor(config: AuthConfig) {
    this.api = new ApiRequestHandler(config);
  }

  async getSummaries(_params: AnalyticsQueryParams = {}): Promise<SummariesResponse> {
    const params = AnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<SummariesResponse>("/v1/analytics/summaries", params);
  }

  async getCliSummary(_params: AnalyticsQueryParams = {}): Promise<SummariesResponse> {
    const params = AnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<SummariesResponse>("/v1/analytics/cli-summary", params);
  }

  async getUsers(_params: AnalyticsQueryParams = {}): Promise<UsersListResponse> {
    const params = AnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<UsersListResponse>("/v1/analytics/users", params);
  }

  async getAssistantsChats(
    _params: AttributesAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = toQueryParams(AttributesAnalyticsQueryParamsSchema.parse(_params));
    return this.api.get<TabularResponse>("/v1/analytics/assistants-chats", params);
  }

  async getWorkflows(_params: AttributesAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = toQueryParams(AttributesAnalyticsQueryParamsSchema.parse(_params));
    return this.api.get<TabularResponse>("/v1/analytics/workflows", params);
  }

  async getAssistantsRequests(
    _params: AssistantsRequestsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = toQueryParams(AssistantsRequestsQueryParamsSchema.parse(_params));
    return this.api.get<TabularResponse>("/v1/analytics/assistants-requests", params);
  }

  async getWorkflowsExecutions(
    _params: AttributesAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = toQueryParams(AttributesAnalyticsQueryParamsSchema.parse(_params));
    return this.api.get<TabularResponse>("/v1/analytics/workflows-executions", params);
  }

  async getAttributesUsage(_params: AttributesUsageQueryParams): Promise<TabularResponse> {
    const params = toQueryParams(AttributesUsageQueryParamsSchema.parse(_params));
    return this.api.get<TabularResponse>("/v1/analytics/attributes-usage", params);
  }

  async getToolsUsage(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/tools-usage", params);
  }

  async getWebhooksInvocation(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/webhooks-invocation", params);
  }

  async getMcpServers(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/mcp-servers", params);
  }

  async getMcpServersByUsers(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/mcp-servers-by-users", params);
  }

  async getProjectsSpending(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/projects-spending", params);
  }

  async getLlmsUsage(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/llms-usage", params);
  }

  async getUsersSpending(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/users-spending", params);
  }

  async getBudgetSoftLimit(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/budget-soft-limit", params);
  }

  async getBudgetHardLimit(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/budget-hard-limit", params);
  }

  async getUsersActivity(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/users-activity", params);
  }

  async getProjectsActivity(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/projects-activity", params);
  }

  async getAgentsUsage(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/agents-usage", params);
  }

  async getCliAgents(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/cli-agents", params);
  }

  async getCliLlms(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/cli-llms", params);
  }

  async getCliUsers(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/cli-users", params);
  }

  async getCliErrors(_params: PaginatedAnalyticsQueryParams = {}): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/cli-errors", params);
  }

  async getCliRepositories(
    _params: PaginatedAnalyticsQueryParams = {},
  ): Promise<TabularResponse> {
    const params = PaginatedAnalyticsQueryParamsSchema.parse(_params);
    return this.api.get<TabularResponse>("/v1/analytics/cli-repositories", params);
  }
}
