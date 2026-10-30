import { AssistantMapper } from "../mappers/assistant.mapper";
import type {
  Assistant,
  AssistantBase,
  AssistantVersion,
  BaseModelApiResponse,
  BaseModelResponse,
  ToolKitDetails,
  AssistantCreateResponse,
  AssistantCreateApiResponse,
  AssistantUpdateResponse,
} from "../models/assistant";
import type { AnyJson, AuthConfig, PaginatedResponse } from "../models/common";
import { z } from "zod";
import {
  AssistantChatParamsSchema,
  VirtualAssistantChatParamsSchema,
  type AssistantCreateParams,
  AssistantCreateParamsSchema,
  type AssistantEvaluationParams,
  AssistantEvaluationParamsSchema,
  type AssistantListParams,
  AssistantListParamsSchema,
  type AssistantUpdateParams,
  AssistantUpdateParamsSchema,
  type AssistantChatParams,
  type VirtualAssistantChatParams,
  AssistantVersionsListParamsSchema,
  type AssistantVersionsListParams,
} from "../schemas/assistant";
import { ApiRequestHandler } from "../utils/http";

// Union of supported response shapes for versions list endpoint to avoid `any`.
// - Backend may return a raw array, or wrap in {data: [...]}, or {versions: [...]}.
export type VersionsListResponse =
  | AssistantVersion[]
  | { data: AssistantVersion[];[key: string]: unknown }
  | { versions: AssistantVersion[];[key: string]: unknown }
  | { items: AssistantVersion[];[key: string]: unknown };

export class AssistantService {
  private api: ApiRequestHandler;

  constructor(config: AuthConfig) {
    this.api = new ApiRequestHandler(config);
  }

  /**
   * Get list of available assistants.
   */
  async list(_params: AssistantListParams = {}): Promise<(Assistant | AssistantBase)[]> {
    const params = AssistantListParamsSchema.parse(_params);

    const response = await this.api.get<PaginatedResponse<Assistant | AssistantBase>>(
      "/v1/assistants",
      {
        ...params,
        ...(params.filters ? { filters: JSON.stringify(params.filters) } : {}),
      },
    );

    return response.data;
  }

  /**
   * Get list of available assistants with pagination metadata.
   */
  async listPaginated(
    _params: AssistantListParams = {},
  ): Promise<PaginatedResponse<Assistant | AssistantBase>> {
    const params = AssistantListParamsSchema.parse(_params);

    const response = await this.api.get<PaginatedResponse<Assistant | AssistantBase>>(
      "/v1/assistants",
      {
        ...params,
        ...(params.filters ? { filters: JSON.stringify(params.filters) } : {}),
      },
    );

    return response;
  }

  /**
   * Get assistant by ID.
   */
  async get(assistantId: string): Promise<Assistant> {
    return this.api.get<Assistant>(`/v1/assistants/id/${assistantId}`);
  }

  /**
   * Get assistant by slug.
   */
  async getBySlug(slug: string): Promise<Assistant> {
    return this.api.get<Assistant>(`/v1/assistants/slug/${slug}`);
  }

  /**
   * Create a new assistant.
   * @returns AssistantCreateResponse with assistant_id and optional validation results
   */
  async create(_params: AssistantCreateParams): Promise<AssistantCreateResponse> {
    const params = { ..._params };

    // Ensure is_global is a boolean, default to false if not
    if ("is_global" in params && typeof params.is_global !== "boolean") {
      params.is_global = false;
    }

    const validatedParams = AssistantCreateParamsSchema.parse(params);
    const response = await this.api.post<AssistantCreateApiResponse>("/v1/assistants", validatedParams);
    return AssistantMapper.mapCreateResponse(response);
  }

  /**
   * Update an existing assistant.
   * @returns AssistantUpdateResponse with optional validation results
   */
  async update(
    assistantId: string,
    _params: AssistantUpdateParams,
  ): Promise<AssistantUpdateResponse> {
    const params = { ..._params };

    // Ensure is_global is a boolean, default to false if not
    if ("is_global" in params && typeof params.is_global !== "boolean") {
      params.is_global = false;
    }

    const validatedParams = AssistantUpdateParamsSchema.parse(params);
    return this.api.put<AssistantUpdateResponse>(`/v1/assistants/${assistantId}`, validatedParams);
  }

  /**
   * Get list of available tools.
   */
  async getTools(): Promise<ToolKitDetails[]> {
    return this.api.get<ToolKitDetails[]>("/v1/assistants/tools");
  }

  /**
   * Delete an assistant by ID.
   */
  async delete(assistantId: string): Promise<AnyJson> {
    return this.api.delete(`/v1/assistants/${assistantId}`);
  }

  /**
   * Get list of prebuilt assistants.
   */
  async getPrebuilt(): Promise<Assistant[]> {
    return this.api.get<Assistant[]>("/v1/assistants/prebuilt");
  }

  /**
   * Get prebuilt assistant by slug.
   */
  async getPrebuiltBySlug(slug: string): Promise<Assistant> {
    return this.api.get<Assistant>(`/v1/assistants/prebuilt/${slug}`);
  }

  /**
   * List assistant versions.
   */
  async listVersions(
    assistantId: string,
    _params: AssistantVersionsListParams = {},
  ): Promise<AssistantVersion[]> {
    const params = AssistantVersionsListParamsSchema.parse(_params);
    const response = await this.api.get<VersionsListResponse>(
      `/v1/assistants/${assistantId}/versions`,
      params,
    );
    // Support multiple backend response shapes: array, {data: [...]}, {versions: [...]}, {items: [...]}.
    if (Array.isArray(response)) {
      return response;
    }
    if (response && "data" in response && Array.isArray(response.data)) {
      return response.data;
    }
    if (
      response &&
      "versions" in response &&
      Array.isArray((response as { versions: unknown }).versions)
    ) {
      return (response as { versions: AssistantVersion[] }).versions;
    }
    if (response && "items" in response && Array.isArray((response as { items: unknown }).items)) {
      return (response as { items: AssistantVersion[] }).items;
    }
    return [];
  }

  /**
   * Get a specific assistant version by number.
   */
  async getVersion(assistantId: string, versionNumber: number): Promise<AssistantVersion> {
    return this.api.get<AssistantVersion>(
      `/v1/assistants/${assistantId}/versions/${versionNumber}`,
    );
  }

  /**
   * Send a chat request to an assistant.
   */
  async chat(
    assistantId: string,
    _params: AssistantChatParams,
    headers?: Record<string, string>,
  ): Promise<BaseModelResponse> {
    let zodSchema: z.ZodType | undefined = undefined;
    let params = { ..._params };

    if (params.output_schema && params.output_schema instanceof z.ZodType) {
      zodSchema = params.output_schema as z.ZodType;
      // Convert Zod schema to JSON schema
      params.output_schema = z.toJSONSchema(zodSchema);
    }

    params = AssistantChatParamsSchema.parse(params);

    const response = await this.api.post<BaseModelApiResponse>(
      `/v1/assistants/${assistantId}/model`,
      params,
      {
        responseType: params.stream ? "stream" : undefined,
      },
      headers,
    );

    const mapped = AssistantMapper.mapBaseModelApiResponse(response);

    if (!params.stream && zodSchema && mapped.generated) {
      mapped.generated = zodSchema.parse(mapped.generated);
    }

    return mapped;
  }

  /**
   * Send a chat request to an assistant by slug.
   */
  async chatBySlug(
    assistantSlug: string,
    _params: AssistantChatParams,
    headers?: Record<string, string>,
  ): Promise<BaseModelResponse> {
    let zodSchema: z.ZodType | undefined = undefined;
    let params = { ..._params };

    if (params.output_schema && params.output_schema instanceof z.ZodType) {
      zodSchema = params.output_schema as z.ZodType;
      params.output_schema = z.toJSONSchema(zodSchema);
    }

    params = AssistantChatParamsSchema.parse(params);

    const response = await this.api.post<BaseModelApiResponse>(
      `/v1/assistants/slug/${assistantSlug}/model`,
      params,
      {
        responseType: params.stream ? "stream" : undefined,
      },
      headers,
    );
    const mapped = AssistantMapper.mapBaseModelApiResponse(response);

    if (!params.stream && zodSchema && mapped.generated) {
      mapped.generated = zodSchema.parse(mapped.generated);
    }

    return mapped;
  }

  /**
   * Run inference using an inline (virtual) assistant definition.
   * No database assistant record is required. History is never persisted.
   */
  async askVirtual(
    _params: VirtualAssistantChatParams,
    headers?: Record<string, string>,
  ): Promise<BaseModelResponse> {
    let zodSchema: z.ZodType | undefined = undefined;
    let params = { ..._params };

    if (params.output_schema && params.output_schema instanceof z.ZodType) {
      zodSchema = params.output_schema as z.ZodType;
      params.output_schema = z.toJSONSchema(zodSchema);
    }

    params = VirtualAssistantChatParamsSchema.parse(params);

    const response = await this.api.post<BaseModelApiResponse>(
      "/v1/assistants/virtual/model",
      params,
      {
        responseType: params.stream ? "stream" : undefined,
      },
      headers,
    );

    const mapped = AssistantMapper.mapBaseModelApiResponse(response);

    if (!params.stream && zodSchema && mapped.generated) {
      mapped.generated = zodSchema.parse(mapped.generated);
    }

    return mapped;
  }

  /**
   * Compare two assistant versions.
   */
  async compareVersions(
    assistantId: string,
    v1: number,
    v2: number,
  ): Promise<Record<string, unknown>> {
    return this.api.get<Record<string, unknown>>(
      `/v1/assistants/${assistantId}/versions/${v1}/compare/${v2}`,
    );
  }

  /**
   * Rollback assistant to a specific version. Creates a new version mirroring the target.
   */
  async rollbackToVersion(assistantId: string, versionNumber: number): Promise<AnyJson> {
    return this.api.post<AnyJson>(
      `/v1/assistants/${assistantId}/versions/${versionNumber}/rollback`,
      {},
    );
  }

  /**
   * Send a chat request to a specific assistant version.
   */
  async chatWithVersion(
    assistantId: string,
    versionNumber: number,
    _params: AssistantChatParams,
  ): Promise<BaseModelResponse> {
    let zodSchema: z.ZodType | undefined = undefined;
    let params = { ..._params };

    if (params.output_schema && params.output_schema instanceof z.ZodType) {
      zodSchema = params.output_schema as z.ZodType;
      params.output_schema = z.toJSONSchema(zodSchema);
    }

    params = AssistantChatParamsSchema.parse(params);

    // Use stable chat endpoint and pass version in body for broader backend compatibility
    const response = await this.api.post<BaseModelApiResponse>(
      `/v1/assistants/${assistantId}/model`,
      { ...params, version: versionNumber },
      {
        responseType: params.stream ? "stream" : undefined,
      },
    );

    const mapped = AssistantMapper.mapBaseModelApiResponse(response);

    if (!params.stream && zodSchema && mapped.generated) {
      mapped.generated = zodSchema.parse(mapped.generated);
    }

    return mapped;
  }

  /**
   * Evaluate an assistant with a dataset.
   */
  async evaluate(assistantId: string, _params: AssistantEvaluationParams): Promise<AnyJson> {
    const params = AssistantEvaluationParamsSchema.parse(_params);
    return this.api.post(`/v1/assistants/${assistantId}/evaluate`, params);
  }
}
