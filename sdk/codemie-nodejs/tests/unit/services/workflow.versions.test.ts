import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { WorkflowService } from "../../../src/services/workflow";
import { ApiRequestHandler } from "../../../src/utils/http";
import type {
  WorkflowRevisionCreatedBy,
  WorkflowVersionHistoryResponse,
} from "../../../src/models/workflow";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("WorkflowService versions", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: WorkflowService;
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
    service = new WorkflowService({ apiDomain: domain, token });
  });

  it("WorkflowRevisionCreatedBy is keyed by user_id, not BaseUser's id", () => {
    const createdBy: WorkflowRevisionCreatedBy = {
      user_id: "u1",
      username: "alice",
      name: "Alice",
    };
    // @ts-expect-error revision creators carry user_id on the wire, not id
    const legacy: WorkflowRevisionCreatedBy = { id: "u1", username: "alice", name: "Alice" };

    expect(createdBy.user_id).toBe("u1");
    expect(legacy).toBeDefined();
  });

  it("listVersions should call correct endpoint and return history response", async () => {
    const response: WorkflowVersionHistoryResponse = {
      workflow_id: "wf-123",
      workflow_name: "My Workflow",
      total_revisions: 1,
      revisions: [
        {
          revision_index: 0,
          yaml_config: "steps: []",
          date: "2026-08-27T10:00:00",
          created_by: { user_id: "u1", username: "alice", name: "Alice" },
          change_notes: null,
        },
      ],
    };

    apiHandler.get.mockResolvedValue(response);

    const result = await service.listVersions("wf-123");

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions");
    expect(result).toEqual(response);
  });

  it("listVersions should send page and per_page when given", async () => {
    apiHandler.get.mockResolvedValue({
      workflow_id: "wf-123",
      workflow_name: "My Workflow",
      total_revisions: 22,
      revisions: [
        {
          revision_index: 20,
          yaml_config: "steps: []",
          date: "2026-08-27T10:00:00",
          created_by: null,
          change_notes: null,
        },
      ],
    } satisfies WorkflowVersionHistoryResponse);

    const result = await service.listVersions("wf-123", { page: 1, per_page: 20 });

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions", {
      page: 1,
      per_page: 20,
    });
    // Positions are absolute in the full history, not offsets into the page.
    expect(result.revisions[0].revision_index).toBe(20);
    expect(result.total_revisions).toBe(22);
  });

  it("listVersions should send only the given paging param", async () => {
    apiHandler.get.mockResolvedValue({} as WorkflowVersionHistoryResponse);

    await service.listVersions("wf-123", { per_page: 5 });
    expect(apiHandler.get).toHaveBeenLastCalledWith("/v1/workflows/wf-123/versions", {
      per_page: 5,
    });

    await service.listVersions("wf-123", { page: 3 });
    expect(apiHandler.get).toHaveBeenLastCalledWith("/v1/workflows/wf-123/versions", { page: 3 });
  });

  it("listVersions should send page 0 rather than dropping it as falsy", async () => {
    apiHandler.get.mockResolvedValue({} as WorkflowVersionHistoryResponse);

    await service.listVersions("wf-123", { page: 0 });

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions", { page: 0 });
  });

  it("listVersions should leave paging bounds to the API", async () => {
    apiHandler.get.mockResolvedValue({} as WorkflowVersionHistoryResponse);

    await service.listVersions("wf-123", { page: -1, per_page: 101 });

    expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions", {
      page: -1,
      per_page: 101,
    });
  });

  it("listVersions should pass through revisions without a creator", async () => {
    const response: WorkflowVersionHistoryResponse = {
      workflow_id: "wf-123",
      workflow_name: "My Workflow",
      total_revisions: 1,
      revisions: [
        {
          revision_index: 0,
          yaml_config: "steps: []",
          date: "2026-08-27T10:00:00",
          created_by: null,
          change_notes: null,
        },
      ],
    };

    apiHandler.get.mockResolvedValue(response);

    const result = await service.listVersions("wf-123");

    expect(result.revisions[0].created_by).toBeNull();
  });

  it("rollback should call correct endpoint with revision_index", async () => {
    const resp = { message: "Workflow wf-123 rolled back to revision 0." };
    apiHandler.post.mockResolvedValue(resp);

    const result = await service.rollback("wf-123", 0);

    expect(apiHandler.post).toHaveBeenCalledWith("/v1/workflows/wf-123/versions/rollback", {
      revision_index: 0,
    });
    expect(result).toEqual(resp);
  });

  it("rollback should include change_notes when provided", async () => {
    const resp = { message: "Workflow wf-123 rolled back to revision 1." };
    apiHandler.post.mockResolvedValue(resp);

    const result = await service.rollback("wf-123", 1, "Reverting bad config");

    expect(apiHandler.post).toHaveBeenCalledWith("/v1/workflows/wf-123/versions/rollback", {
      revision_index: 1,
      change_notes: "Reverting bad config",
    });
    expect(result).toEqual(resp);
  });

  it("rollback should reject negative revision_index", async () => {
    await expect(service.rollback("wf-123", -1)).rejects.toThrow();
  });
});
