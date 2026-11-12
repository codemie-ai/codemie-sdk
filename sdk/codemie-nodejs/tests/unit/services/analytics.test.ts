import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { AnalyticsService } from "../../../src/services/analytics";
import { ApiRequestHandler } from "../../../src/utils/http";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("AnalyticsService run attributes", () => {
  const apiDomain = "https://api.example.com";
  const token = "test-token";
  let service: AnalyticsService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  const lastParams = (): Record<string, unknown> => {
    const calls = (apiHandler.get as jest.Mock).mock.calls;
    return calls[calls.length - 1][1] as Record<string, unknown>;
  };

  beforeEach(() => {
    apiHandler = {
      get: jest.fn().mockResolvedValue({ data: { columns: [], rows: [] } } as never),
    } as unknown as jest.Mocked<ApiRequestHandler>;
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
    service = new AnalyticsService({ apiDomain, token });
  });

  it("getAssistantsChats sends attributes as a JSON string", async () => {
    await service.getAssistantsChats({ attributes: { team: "alpha" } });

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/analytics/assistants-chats",
      expect.objectContaining({ attributes: '{"team":"alpha"}' }),
    );
  });

  it("getWorkflows sends attributes as a JSON string", async () => {
    await service.getWorkflows({ attributes: { team: "alpha" } });

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/analytics/workflows",
      expect.objectContaining({ attributes: '{"team":"alpha"}' }),
    );
  });

  it("round-trips quote and non-ASCII values", async () => {
    const attributes = { team: 'ålpha "x"' };
    await service.getAssistantsChats({ attributes });

    expect(JSON.parse(lastParams().attributes as string)).toEqual(attributes);
  });

  it("omits attributes when not provided and keeps pagination defaults", async () => {
    await service.getAssistantsChats({});

    const params = lastParams();
    expect("attributes" in params).toBe(false);
    expect(params.page).toBe(0);
    expect(params.per_page).toBe(20);
  });

  it("sends empty attributes as '{}'", async () => {
    await service.getWorkflows({ attributes: {} });

    expect(lastParams().attributes).toBe("{}");
  });

  it("getAssistantsRequests uses its endpoint and params", async () => {
    await service.getAssistantsRequests({
      client_source: "platform",
      assistant_id: "a1",
      attributes: { team: "alpha" },
    });

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/analytics/assistants-requests",
      expect.objectContaining({
        client_source: "platform",
        assistant_id: "a1",
        attributes: '{"team":"alpha"}',
      }),
    );
  });

  it("getWorkflowsExecutions uses its endpoint and params", async () => {
    await service.getWorkflowsExecutions({
      client_source: "other",
      attributes: { team: "alpha" },
    });

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/analytics/workflows-executions",
      expect.objectContaining({
        client_source: "other",
        attributes: '{"team":"alpha"}',
      }),
    );
  });

  it("getAttributesUsage uses its endpoint and requires attribute_key", async () => {
    await service.getAttributesUsage({
      attribute_key: "team",
      attributes: { env: "prod" },
    });

    expect(apiHandler.get).toHaveBeenCalledWith(
      "/v1/analytics/attributes-usage",
      expect.objectContaining({
        attribute_key: "team",
        attributes: '{"env":"prod"}',
      }),
    );

    await expect(service.getAttributesUsage({} as any)).rejects.toThrow();
  });

  it("getToolsUsage does not send attributes", async () => {
    await service.getToolsUsage({ attributes: { team: "alpha" } } as any);

    expect("attributes" in lastParams()).toBe(false);
  });
});
