import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { AssistantService } from "../../../src/services/assistant";
import { ApiRequestHandler } from "../../../src/utils/http";
import {
  type Assistant,
  type AssistantBase,
  type BaseModelApiResponse,
  ChatRole,
  type ToolKitDetails,
} from "../../../src/models";
import type {
  AssistantChatParams,
  AssistantCreateParams,
  AssistantEvaluationParams,
  AssistantUpdateParams,
} from "../../../src/schemas";
import { ApiError, NotFoundError } from "../../../src/exceptions";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("AssistantService", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: AssistantService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  const mockBaseAssistant: AssistantBase = {
    id: "1",
    name: "Test Assistant",
    description: "Test Description",
  };

  const mockAssistant: Assistant = {
    ...mockBaseAssistant,
    system_prompt: "You are a helpful assistant",
    system_prompt_history: [],
    project: "test-project",
    llm_model_type: "gpt-4",
    toolkits: [],
    conversation_starters: [],
    shared: false,
    is_react: false,
    is_global: false,
    creator: "test-user",
    context: [],
    mcp_servers: [],
    assistant_ids: [],
    nested_assistants: [],
  };

  beforeEach(() => {
    apiHandler = {
      client: {},
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      stream: jest.fn(),
      request: jest.fn(),
      throwIfResponseError: jest.fn(),
    } as unknown as jest.Mocked<ApiRequestHandler>;

    service = new AssistantService({ apiDomain: domain, token });
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
  });

  describe("constructor", () => {
    it("should initialize with default SSL verification", () => {
      const service = new AssistantService({ apiDomain: domain, token });
      expect(ApiRequestHandler).toHaveBeenCalledWith({ apiDomain: domain, token });
    });

    it("should initialize with SSL verification disabled", () => {
      const service = new AssistantService({ apiDomain: domain, token, verifySSL: false });
      expect(ApiRequestHandler).toHaveBeenCalledWith({
        apiDomain: domain,
        token,
        verifySSL: false,
      });
    });
  });

  describe("list", () => {
    const mockAssistants: AssistantBase[] = [mockBaseAssistant];

    it("should get list of assistants with default parameters", async () => {
      apiHandler.get.mockResolvedValue({ data: mockAssistants });

      const result = await service.list();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants", {
        minimal_response: true,
        page: 0,
        per_page: 12,
        scope: "visible_to_user",
      });
      expect(result).toEqual(mockAssistants);
    });

    it("should get list of assistants with custom parameters", async () => {
      apiHandler.get.mockResolvedValue({ data: mockAssistants });

      const params = {
        minimal_response: false,
        scope: "marketplace" as const,
        page: 1,
        per_page: 20,
        filters: { name: "test" },
      };

      const result = await service.list(params);

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants", {
        minimal_response: false,
        scope: "marketplace",
        page: 1,
        per_page: 20,
        filters: JSON.stringify({ name: "test" }),
      });
      expect(result).toEqual(mockAssistants);
    });

    it("should handle empty result", async () => {
      apiHandler.get.mockResolvedValue({ data: [] });
      const result = await service.list();
      expect(result).toEqual([]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch assistants");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.list()).rejects.toThrow(error);
    });
  });

  describe("get", () => {
    it("should get assistant by ID", async () => {
      apiHandler.get.mockResolvedValue(mockAssistant);

      const result = await service.get("1");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/id/1");
      expect(result).toEqual(mockAssistant);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Assistant", "non-existent");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.get("non-existent")).rejects.toThrow(error);
    });
  });

  describe("getBySlug", () => {
    const slugAssistant: Assistant = {
      ...mockAssistant,
      slug: "test-assistant",
    };

    it("should get assistant by slug", async () => {
      apiHandler.get.mockResolvedValue(slugAssistant);

      const result = await service.getBySlug("test-assistant");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/slug/test-assistant");
      expect(result).toEqual(slugAssistant);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Assistant", "non-existent-slug");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.getBySlug("non-existent-slug")).rejects.toThrow(error);
    });
  });

  describe("create", () => {
    const createRequest: AssistantCreateParams = {
      name: "New Assistant",
      description: "New Description",
      system_prompt: "You are a helpful assistant",
      project: "test-project",
      llm_model_type: "gpt-4",
      toolkits: [],
      conversation_starters: [],
      context: [],
      mcp_servers: [],
      assistant_ids: [],
      prompt_variables: [
        { key: "project_name", default_value: "Delta", description: "Project name" },
      ],
      skip_integration_validation: false,
    };

    it("should create new assistant", async () => {
      const mockResponse = { id: "123", success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.create(createRequest);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/assistants", createRequest);
      expect(result).toEqual({ ...mockResponse, assistant_id: "123" });
    });

    it("should preserve mcp_config_id in outbound create payload", async () => {
      const requestWithSavedConfigMcp: AssistantCreateParams = {
        ...createRequest,
        mcp_servers: [
          {
            name: "RI-logs",
            description: "Download, unzip and grep log files",
            enabled: true,
            mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
            resolve_dynamic_values_in_arguments: false,
            tools: ["fetch_logs"],
          },
        ],
      };

      apiHandler.post.mockResolvedValue({ id: "123", success: true });

      await service.create(requestWithSavedConfigMcp);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants",
        expect.objectContaining({
          mcp_servers: [
            expect.objectContaining({
              name: "RI-logs",
              mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
            }),
          ],
        }),
      );
    });

    it("should forward an undeclared mcp_servers key in the outbound create payload", async () => {
      const requestWithUnknownMcpField: AssistantCreateParams = {
        ...createRequest,
        mcp_servers: [
          {
            name: "RI-logs",
            enabled: true,
            future_backend_field: "x",
          },
        ],
      };

      apiHandler.post.mockResolvedValue({ id: "123", success: true });

      await service.create(requestWithUnknownMcpField);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants",
        expect.objectContaining({
          mcp_servers: [expect.objectContaining({ future_backend_field: "x" })],
        }),
      );
    });

    it("should handle API errors during creation", async () => {
      const error = new ApiError("Creation failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.create(createRequest)).rejects.toThrow(error);
    });
  });

  describe("update", () => {
    const updateRequest: AssistantUpdateParams = {
      name: "Updated Assistant",
      description: "Updated Description",
      system_prompt: "Updated prompt",
      project: "test-project",
      llm_model_type: "gpt-4",
      toolkits: [],
      conversation_starters: [],
      context: [],
      mcp_servers: [],
      assistant_ids: [],
      prompt_variables: [
        { key: "project_name", default_value: "Omega" },
        { key: "region", default_value: "eu" },
      ],
      skip_integration_validation: false,
    };

    it("should update existing assistant", async () => {
      const mockResponse = { success: true };
      apiHandler.put.mockResolvedValue(mockResponse);

      const result = await service.update("123", updateRequest);

      expect(apiHandler.put).toHaveBeenCalledWith("/v1/assistants/123", updateRequest);
      expect(result).toEqual(mockResponse);
    });

    it("should preserve mcp_config_id in outbound update payload", async () => {
      const requestWithSavedConfigMcp: AssistantUpdateParams = {
        ...updateRequest,
        mcp_servers: [
          {
            name: "RI-logs",
            description: "Download, unzip and grep log files",
            enabled: true,
            mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
            resolve_dynamic_values_in_arguments: false,
            tools: ["fetch_logs"],
          },
        ],
      };

      apiHandler.put.mockResolvedValue({ success: true });

      await service.update("123", requestWithSavedConfigMcp);

      expect(apiHandler.put).toHaveBeenCalledWith(
        "/v1/assistants/123",
        expect.objectContaining({
          mcp_servers: [
            expect.objectContaining({
              name: "RI-logs",
              mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
            }),
          ],
        }),
      );
    });

    it("should forward an undeclared mcp_servers key in the outbound update payload", async () => {
      const requestWithUnknownMcpField: AssistantUpdateParams = {
        ...updateRequest,
        mcp_servers: [
          {
            name: "RI-logs",
            enabled: true,
            future_backend_field: "x",
          },
        ],
      };

      apiHandler.put.mockResolvedValue({ success: true });

      await service.update("123", requestWithUnknownMcpField);

      expect(apiHandler.put).toHaveBeenCalledWith(
        "/v1/assistants/123",
        expect.objectContaining({
          mcp_servers: [expect.objectContaining({ future_backend_field: "x" })],
        }),
      );
    });

    it("should handle API errors during update", async () => {
      const error = new ApiError("Update failed");
      apiHandler.put.mockRejectedValue(error);
      await expect(service.update("123", updateRequest)).rejects.toThrow(error);
    });
  });

  describe("getTools", () => {
    const mockTools: ToolKitDetails[] = [
      {
        toolkit: "code",
        label: "Code Tools",
        settings_config: false,
        is_external: false,
        tools: [
          {
            name: "code_search",
            settings_config: false,
          },
        ],
      },
    ];

    it("should get list of available tools", async () => {
      apiHandler.get.mockResolvedValue(mockTools);

      const result = await service.getTools();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/tools");
      expect(result).toEqual(mockTools);
    });

    it("should handle empty tools list", async () => {
      apiHandler.get.mockResolvedValue([]);
      const result = await service.getTools();
      expect(result).toEqual([]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch tools");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.getTools()).rejects.toThrow(error);
    });
  });

  describe("delete", () => {
    it("should delete assistant by ID", async () => {
      const mockResponse = { success: true };
      apiHandler.delete.mockResolvedValue(mockResponse);

      const result = await service.delete("123");

      expect(apiHandler.delete).toHaveBeenCalledWith("/v1/assistants/123");
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during deletion", async () => {
      const error = new ApiError("Deletion failed");
      apiHandler.delete.mockRejectedValue(error);
      await expect(service.delete("123")).rejects.toThrow(error);
    });
  });

  describe("evaluate", () => {
    const evaluateRequest: AssistantEvaluationParams = {
      dataset_id: "dataset-123",
      experiment_name: "exp-1",
      system_prompt: "You are a helpful assistant",
      llm_model: "gpt-4",
    };

    it("should evaluate an assistant", async () => {
      const mockResponse = { success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.evaluate("123", evaluateRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/evaluate",
        evaluateRequest,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should evaluate an assistant without optional fields", async () => {
      const mockResponse = { success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const { dataset_id, experiment_name } = evaluateRequest;
      await service.evaluate("123", { dataset_id, experiment_name });

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/assistants/123/evaluate", {
        dataset_id,
        experiment_name,
      });
    });

    it("should handle API errors during evaluation", async () => {
      const error = new ApiError("Evaluation failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.evaluate("123", evaluateRequest)).rejects.toThrow(error);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Assistant", "123");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.evaluate("123", evaluateRequest)).rejects.toThrow(error);
    });
  });

  describe("getPrebuilt", () => {
    const prebuiltAssistant: Assistant = {
      ...mockAssistant,
      shared: true,
      is_global: true,
      creator: "system",
    };

    it("should get list of prebuilt assistants", async () => {
      apiHandler.get.mockResolvedValue([prebuiltAssistant]);

      const result = await service.getPrebuilt();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/prebuilt");
      expect(result).toEqual([prebuiltAssistant]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch prebuilt assistants");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.getPrebuilt()).rejects.toThrow(error);
    });
  });

  describe("getPrebuiltBySlug", () => {
    const prebuiltAssistant: Assistant = {
      ...mockAssistant,
      shared: true,
      is_global: true,
      creator: "system",
      slug: "prebuilt-assistant",
    };

    it("should get prebuilt assistant by slug", async () => {
      apiHandler.get.mockResolvedValue(prebuiltAssistant);

      const result = await service.getPrebuiltBySlug("prebuilt-assistant");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/prebuilt/prebuilt-assistant");
      expect(result).toEqual(prebuiltAssistant);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Prebuilt Assistant", "non-existent");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.getPrebuiltBySlug("non-existent")).rejects.toThrow(error);
    });
  });

  describe("chat", () => {
    const chatRequest: AssistantChatParams = {
      text: "Hello assistant",
      history: [
        { role: ChatRole.USER, message: "Hello" },
        { role: ChatRole.ASSISTANT, message: "Hi there!" },
      ],
      stream: false,
    };

    it("should send chat request with streaming disabled", async () => {
      const mockResponse: BaseModelApiResponse = {
        generated: "Hello! How can I help you today?",
        timeElapsed: 0.5,
        tokensUsed: 15,
      };

      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", chatRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        chatRequest,
        {
          responseType: undefined,
        },
        undefined,
      );
      expect(result).toEqual({
        generated: mockResponse.generated,
        time_elapsed: mockResponse.timeElapsed,
        tokens_used: mockResponse.tokensUsed,
      });
    });

    it("should send chat request with streaming enabled", async () => {
      const streamRequest = { ...chatRequest, stream: true };
      const mockResponse = { data: "streaming-data" };
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", streamRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        streamRequest,
        {
          responseType: "stream",
        },
        undefined,
      );
      expect(result).toEqual({});
    });

    it("should handle chat API errors", async () => {
      const error = new ApiError("Chat request failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.chat("123", chatRequest)).rejects.toThrow(error);
    });

    it("should handle chat history as string", async () => {
      const stringHistoryRequest: AssistantChatParams = {
        ...chatRequest,
        history: JSON.stringify(chatRequest.history),
      };

      const mockResponse: BaseModelApiResponse = {
        generated: "Response",
        tokensUsed: 5,
      };

      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", stringHistoryRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        stringHistoryRequest,
        { responseType: undefined },
        undefined,
      );
      expect(result).toEqual({
        generated: mockResponse.generated,
        tokens_used: mockResponse.tokensUsed,
      });
    });

    it("should send chat request with save_history=true", async () => {
      const saveHistoryRequest: AssistantChatParams = {
        ...chatRequest,
        save_history: true,
      };

      const mockResponse: BaseModelApiResponse = {
        generated: "Response",
        tokensUsed: 10,
      };

      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", saveHistoryRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        saveHistoryRequest,
        { responseType: undefined },
        undefined,
      );
      expect(result).toEqual({
        generated: mockResponse.generated,
        tokens_used: mockResponse.tokensUsed,
      });
    });

    it("should send chat request with save_history=false", async () => {
      const noSaveHistoryRequest: AssistantChatParams = {
        ...chatRequest,
        save_history: false,
      };

      const mockResponse: BaseModelApiResponse = {
        generated: "Response without saving",
        tokensUsed: 8,
      };

      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", noSaveHistoryRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        noSaveHistoryRequest,
        { responseType: undefined },
        undefined,
      );
      expect(result).toEqual({
        generated: mockResponse.generated,
        tokens_used: mockResponse.tokensUsed,
      });
    });

    it("should send chat request without save_history (defaults to backend behavior)", async () => {
      const requestWithoutSaveHistory: AssistantChatParams = {
        text: "Hello",
        history: [],
        stream: false,
      };

      const mockResponse: BaseModelApiResponse = {
        generated: "Response",
        tokensUsed: 5,
      };

      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.chat("123", requestWithoutSaveHistory);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/assistants/123/model",
        requestWithoutSaveHistory,
        { responseType: undefined },
        undefined,
      );
      expect(result).toEqual({
        generated: mockResponse.generated,
        tokens_used: mockResponse.tokensUsed,
      });
    });
  });
});
