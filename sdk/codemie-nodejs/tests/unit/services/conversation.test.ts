import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { ConversationCreateParamsSchema } from "../../../src/schemas/conversation";
import { ConversationService } from "../../../src/services/conversation";
import type { ConversationDetails } from "../../../src/models/conversation";
import { ApiRequestHandler } from "../../../src/utils/http";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("ConversationCreateParamsSchema", () => {
  it("should default mcp_server_single_usage to false when omitted", () => {
    const result = ConversationCreateParamsSchema.parse({});
    expect(result.mcp_server_single_usage).toBe(false);
  });

  it("should preserve mcp_server_single_usage: true when provided", () => {
    const result = ConversationCreateParamsSchema.parse({ mcp_server_single_usage: true });
    expect(result.mcp_server_single_usage).toBe(true);
  });
});

describe("ConversationService.get attributes", () => {
  let apiHandler: jest.Mocked<ApiRequestHandler>;
  let service: ConversationService;

  beforeEach(() => {
    apiHandler = { get: jest.fn() } as unknown as jest.Mocked<ApiRequestHandler>;
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
    service = new ConversationService({ apiDomain: "https://api.example.com", token: "t" });
  });

  it("returns attributes from the details response unchanged", async () => {
    const response = {
      id: "c1",
      conversation_id: "conv1",
      attributes: { team: "alpha" },
    } as unknown as ConversationDetails;
    apiHandler.get.mockResolvedValue(response);

    const result: ConversationDetails = await service.get("conv1");

    expect(result.attributes).toEqual({ team: "alpha" });
  });
});
