import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { AssistantService } from "../../../src/services/assistant";
import { ApiRequestHandler } from "../../../src/utils/http";
import type { AssistantVersion, BaseModelApiResponse } from "../../../src/models";
import type { AssistantChatParams } from "../../../src/schemas";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("AssistantService versions", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: AssistantService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  beforeEach(() => {
    apiHandler = {
      client: {} as any,
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      stream: jest.fn(),
      request: jest.fn(),
      throwIfResponseError: jest.fn(),
    } as unknown as jest.Mocked<ApiRequestHandler>;

    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
    service = new AssistantService({ apiDomain: domain, token });
  });

  it("listVersions should call correct endpoint and return array", async () => {
    const versions: AssistantVersion[] = [
      {
        version_number: 1,
        created_date: new Date().toISOString(),
        system_prompt: "v1",
        context: [],
        toolkits: [],
        mcp_servers: [],
        assistant_ids: [],
        deselected_default_tools: [],
      },
    ];

    apiHandler.get.mockResolvedValue({ data: versions });

    const result = await service.listVersions("assistant-123", { page: 2, per_page: 10 });

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/assistant-123/versions", {
      page: 2,
      per_page: 10,
    });
    expect(result).toEqual(versions);
  });

  it("getVersion should call correct endpoint", async () => {
    const version: AssistantVersion = {
      version_number: 3,
      created_date: new Date().toISOString(),
      system_prompt: "v3",
      context: [],
      toolkits: [],
      mcp_servers: [],
      assistant_ids: [],
      deselected_default_tools: [],
    };

    apiHandler.get.mockResolvedValue(version);

    const result = await service.getVersion("assistant-123", 3);

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/assistants/assistant-123/versions/3");
    expect(result).toEqual(version);
  });

  it("getVersion should default deselected_default_tools to [] when absent", async () => {
    apiHandler.get.mockResolvedValue({
      version_number: 3,
      created_date: new Date().toISOString(),
      system_prompt: "v3",
    });

    const result = await service.getVersion("assistant-123", 3);

    expect(result.deselected_default_tools).toEqual([]);
  });

  it("getVersion should return deselected_default_tools when present", async () => {
    apiHandler.get.mockResolvedValue({
      version_number: 3,
      created_date: new Date().toISOString(),
      system_prompt: "v3",
      deselected_default_tools: ["search_kb"],
    });

    const result = await service.getVersion("assistant-123", 3);

    expect(result.deselected_default_tools).toEqual(["search_kb"]);
  });

  it("compareVersions should call correct endpoint", async () => {
    const diff: Record<string, unknown> = {
      diff: { system_prompt: ["changed"] },
      summary: "system_prompt updated",
    };
    apiHandler.get.mockResolvedValue(diff);

    const result = await service.compareVersions("assistant-123", 1, 2);

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/assistants/assistant-123/versions/1/compare/2",
    );
    expect(result).toEqual(diff);
  });

  it("rollbackToVersion should call correct endpoint", async () => {
    const resp = { status: "ok" };
    apiHandler.post.mockResolvedValue(resp);

    const result = await service.rollbackToVersion("assistant-123", 4);

    expect(apiHandler.post).toHaveBeenCalledWith(
      "/v1/assistants/assistant-123/versions/4/rollback",
      {},
    );
    expect(result).toEqual(resp);
  });

  it("chatWithVersion should call stable endpoint and include version in body", async () => {
    const chatReq: AssistantChatParams = { text: "Hi", history: [], stream: false };
    const mockResponse: BaseModelApiResponse = {
      generated: "Hello",
      timeElapsed: 0.12,
      tokensUsed: 12,
    };

    apiHandler.post.mockResolvedValue(mockResponse);

    const result = await service.chatWithVersion("assistant-123", 2, chatReq);

    expect(apiHandler.post).toHaveBeenCalledWith(
      "/v1/assistants/assistant-123/model",
      { ...chatReq, version: 2 },
      { responseType: undefined },
    );
    expect(result).toEqual({
      generated: mockResponse.generated,
      time_elapsed: mockResponse.timeElapsed,
      tokens_used: mockResponse.tokensUsed,
    });
  });

  it("chatWithVersion should handle stream", async () => {
    const chatReq: AssistantChatParams = { text: "Hi", history: [], stream: true };
    const streamResp = { data: "stream" } as any;
    apiHandler.post.mockResolvedValue(streamResp);

    const result = await service.chatWithVersion("assistant-123", 1, chatReq);

    expect(apiHandler.post).toHaveBeenCalledWith(
      "/v1/assistants/assistant-123/model",
      { ...chatReq, version: 1 },
      { responseType: "stream" },
    );
    expect(result).toEqual({});
  });
});
