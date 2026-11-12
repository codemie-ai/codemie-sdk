import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { WorkflowService } from "../../../src/services/workflow";
import { ApiRequestHandler } from "../../../src/utils/http";
import { PaginatedResponse } from "../../../src/models/common";
import {
  WorkflowMode,
  WorkflowModeType,
  WorkflowResponse,
  WorkflowRevisionCreatedBy,
  WorkflowVersionHistoryResponse,
} from "../../../src/models/workflow";
import {
  WorkflowCreateParams,
  WorkflowEvaluationParams,
  WorkflowUpdateParams,
} from "../../../src/schemas/workflow";
import { WorkflowExecutionService } from "../../../src/services/workflow_execution";
import { ApiError, NotFoundError } from "../../../src/exceptions";
import { omitKeys } from "../helpers";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("WorkflowService", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  let service: WorkflowService;
  let apiHandler: jest.Mocked<ApiRequestHandler>;

  const mockWorkflow: WorkflowResponse = {
    id: "123",
    project: "test-project",
    name: "Test Workflow",
    description: "Test workflow description",
    yaml_config: "steps:\n  - name: step1\n    task: task1",
    mode: WorkflowMode.SEQUENTIAL as WorkflowModeType,
    shared: false,
    date: "2023-01-01",
    update_date: "2023-01-02",
    created_by: {
      username: "user1",
      name: "User One",
    },
  };

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

    service = new WorkflowService({ apiDomain: domain, token });
    (ApiRequestHandler as jest.Mock).mockImplementation(() => apiHandler);
  });

  describe("constructor", () => {
    it("should initialize with default SSL verification", () => {
      new WorkflowService({ apiDomain: domain, token });

      expect(ApiRequestHandler).toHaveBeenCalledWith({ apiDomain: domain, token });
    });

    it("should initialize with SSL verification disabled", () => {
      new WorkflowService({ apiDomain: domain, token, verifySSL: false });

      expect(ApiRequestHandler).toHaveBeenCalledWith({
        apiDomain: domain,
        token,
        verifySSL: false,
      });
    });
  });

  describe("getPrebuilt", () => {
    const prebuiltWorkflow: WorkflowResponse = {
      ...mockWorkflow,
      id: "1",
      name: "Prebuilt Workflow",
      shared: true,
      created_by: {
        username: "system",
        name: "System",
      },
    };

    it("should get list of prebuilt workflows", async () => {
      apiHandler.get.mockResolvedValue([prebuiltWorkflow]);

      const result = await service.getPrebuilt();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/prebuilt");
      expect(result).toEqual([
        {
          ...omitKeys(prebuiltWorkflow, ["date"]),
          created_date: prebuiltWorkflow.date,
        },
      ]);
    });

    it("should handle empty prebuilt list", async () => {
      apiHandler.get.mockResolvedValue([]);

      const result = await service.getPrebuilt();
      expect(result).toEqual([]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch prebuilt workflows");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.getPrebuilt()).rejects.toThrow(error);
    });
  });

  describe("create", () => {
    const createRequest: WorkflowCreateParams = {
      project: "test-project",
      name: "New Workflow",
      description: "Test workflow description",
      yaml_config: "steps:\n  - name: step1\n    task: task1",
      mode: WorkflowMode.SEQUENTIAL as WorkflowModeType,
      shared: false,
    };

    it("should create a new workflow", async () => {
      const mockResponse = { id: "123", success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.create(createRequest);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/workflows", createRequest);
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during creation", async () => {
      const error = new ApiError("Creation failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.create(createRequest)).rejects.toThrow(error);
    });
  });

  describe("update", () => {
    const updateRequest: WorkflowUpdateParams = {
      project: "test-project",
      name: "Updated Workflow",
      description: "Updated description",
      yaml_config: "steps:\n  - name: step1\n    task: updated-task",
      mode: WorkflowMode.AUTONOMOUS as WorkflowModeType,
      shared: true,
    };

    it("should update an existing workflow", async () => {
      const mockResponse = { success: true };
      apiHandler.put.mockResolvedValue(mockResponse);

      const result = await service.update("123", updateRequest);

      expect(apiHandler.put).toHaveBeenCalledWith("/v1/workflows/123", updateRequest);
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during update", async () => {
      const error = new ApiError("Update failed");
      apiHandler.put.mockRejectedValue(error);
      await expect(service.update("123", updateRequest)).rejects.toThrow(error);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Workflow", "123");
      apiHandler.put.mockRejectedValue(error);
      await expect(service.update("123", updateRequest)).rejects.toThrow(error);
    });
  });

  describe("evaluate", () => {
    const evaluateRequest: WorkflowEvaluationParams = {
      dataset_id: "dataset-123",
      experiment_name: "exp-1",
      max_concurrency: 2,
    };

    it("should evaluate a workflow", async () => {
      const mockResponse = { success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.evaluate("123", evaluateRequest);

      expect(apiHandler.post).toHaveBeenCalledWith(
        "/v1/workflows/123/evaluate",
        evaluateRequest,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should apply default max_concurrency", async () => {
      const mockResponse = { success: true };
      apiHandler.post.mockResolvedValue(mockResponse);

      const { dataset_id, experiment_name } = evaluateRequest;
      await service.evaluate("123", { dataset_id, experiment_name } as WorkflowEvaluationParams);

      expect(apiHandler.post).toHaveBeenCalledWith("/v1/workflows/123/evaluate", {
        dataset_id,
        experiment_name,
        max_concurrency: 1,
      });
    });

    it("should handle API errors during evaluation", async () => {
      const error = new ApiError("Evaluation failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.evaluate("123", evaluateRequest)).rejects.toThrow(error);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Workflow", "123");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.evaluate("123", evaluateRequest)).rejects.toThrow(error);
    });
  });

  describe("list", () => {
    const createMockResponse = (data: WorkflowResponse[]): PaginatedResponse<WorkflowResponse> => ({
      data,
      pagination: {
        total: data.length,
        page: 0,
        per_page: 10,
        pages: Math.ceil(data.length / 10),
      },
    });

    it("should list workflows with default parameters", async () => {
      const mockResponse = createMockResponse([mockWorkflow]);
      apiHandler.get.mockResolvedValue(mockResponse);

      const result = await service.list();

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows", {
        page: 0, 
        per_page: 10,
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockWorkflow, ["date"]),
          created_date: mockWorkflow.date,
        },
      ]);
    });

    it("should list workflows with projects filter", async () => {
      const mockResponse = createMockResponse([mockWorkflow]);
      apiHandler.get.mockResolvedValue(mockResponse);

      const projects = ["test-project", "another-project"];
      const result = await service.list({ page: 1, per_page: 20, projects });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows", {
        page: 1,
        per_page: 20,
        filters: JSON.stringify({ project: projects }),
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockWorkflow, ["date"]),
          created_date: mockWorkflow.date,
        },
      ]);
    });

    it("should list workflows with search filter", async () => {
      const mockResponse = createMockResponse([mockWorkflow]);
      apiHandler.get.mockResolvedValue(mockResponse);

      const result = await service.list({ search: "test" });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows", {
        page: 0,
        per_page: 10,
        filters: JSON.stringify({ name: "test" }),
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockWorkflow, ["date"]),
          created_date: mockWorkflow.date,
        },
      ]);
    });

    it("should handle empty list", async () => {
      const mockResponse = createMockResponse([]);
      apiHandler.get.mockResolvedValue(mockResponse);
      const result = await service.list();
      expect(result).toEqual([]);
    });

    it("should handle pagination correctly", async () => {
      const mockWorkflows = [mockWorkflow, { ...mockWorkflow, id: "456" }];
      const mockResponse = createMockResponse(mockWorkflows);
      apiHandler.get.mockResolvedValue(mockResponse);

      const result = await service.list({ page: 0, per_page: 2 });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows", {
        page: 0,
        per_page: 2,
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockWorkflows[0], ["date"]),
          created_date: mockWorkflows[0].date,
        },
        {
          ...omitKeys(mockWorkflows[1], ["date"]),
          created_date: mockWorkflows[1].date,
        },
      ]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch workflows");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.list()).rejects.toThrow(error);
    });
  });

  describe("get", () => {
    it("should get workflow by ID", async () => {
      apiHandler.get.mockResolvedValue(mockWorkflow);

      const result = await service.get("123");

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/id/123");
      expect(result).toEqual({
        ...omitKeys(mockWorkflow, ["date"]),
        created_date: mockWorkflow.date,
      });
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Workflow", "non-existent");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.get("non-existent")).rejects.toThrow(error);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch workflow");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.get("123")).rejects.toThrow(error);
    });
  });

  describe("delete", () => {
    it("should delete workflow by ID", async () => {
      const mockResponse = { success: true };
      apiHandler.delete.mockResolvedValue(mockResponse);

      const result = await service.delete("123");

      expect(apiHandler.delete).toHaveBeenCalledWith("/v1/workflows/123");
      expect(result).toEqual(mockResponse);
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("Workflow", "non-existent");
      apiHandler.delete.mockRejectedValue(error);
      await expect(service.delete("non-existent")).rejects.toThrow(error);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Deletion failed");
      apiHandler.delete.mockRejectedValue(error);
      await expect(service.delete("123")).rejects.toThrow(error);
    });
  });

  describe("run", () => {
    const mockResponse = { execution_id: "456", success: true };
    const workflowId = "123";
    const userInput = "test input";

    it("should run workflow with input", async () => {
      const executionService = new WorkflowExecutionService(apiHandler, workflowId);
      jest.spyOn(service, "executions").mockReturnValue(executionService);
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.run(workflowId, userInput);

      expect(apiHandler.post).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions`,
        {
          user_input: userInput,
          file_name: undefined,
          propagate_headers: undefined,
        },
        {},
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should run workflow without input", async () => {
      const executionService = new WorkflowExecutionService(apiHandler, workflowId);
      jest.spyOn(service, "executions").mockReturnValue(executionService);
      apiHandler.post.mockResolvedValue(mockResponse);

      const result = await service.run(workflowId);

      expect(apiHandler.post).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions`,
        {
          user_input: undefined,
          file_name: undefined,
          propagate_headers: undefined,
        },
        {},
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should run workflow with tags and forward them to create", async () => {
      const executionService = new WorkflowExecutionService(apiHandler, workflowId);
      jest.spyOn(service, "executions").mockReturnValue(executionService);
      apiHandler.post.mockResolvedValue(mockResponse);

      const tags = ["experiment", "sdk-test"];
      const result = await service.run(
        workflowId,
        userInput,
        undefined,
        undefined,
        undefined,
        undefined,
        tags,
      );

      expect(apiHandler.post).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions`,
        {
          user_input: userInput,
          file_name: undefined,
          propagate_headers: undefined,
          tags,
        },
        {},
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during execution", async () => {
      const executionService = new WorkflowExecutionService(apiHandler, workflowId);
      jest.spyOn(service, "executions").mockReturnValue(executionService);

      const error = new ApiError("Execution failed");
      apiHandler.post.mockRejectedValue(error);

      await expect(service.run(workflowId, userInput)).rejects.toThrow(error);
    });
  });

  describe("executions", () => {
    it("should return workflow execution service instance", () => {
      const workflowId = "123";
      const executionService = service.executions(workflowId);

      expect(executionService).toBeInstanceOf(WorkflowExecutionService);
      expect((executionService as any).workflowId).toBe(workflowId);
    });
  });

  describe("versions", () => {
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

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions", {});
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
      expect(apiHandler.get).toHaveBeenLastCalledWith("/v1/workflows/wf-123/versions", {
        page: 3,
      });
    });

    it("listVersions should send page 0 rather than dropping it as falsy", async () => {
      apiHandler.get.mockResolvedValue({} as WorkflowVersionHistoryResponse);

      await service.listVersions("wf-123", { page: 0 });

      expect(apiHandler.get).toHaveBeenCalledWith("/v1/workflows/wf-123/versions", { page: 0 });
    });

    it.each([
      [{ page: -1 }],
      [{ per_page: 0 }],
      [{ per_page: -5 }],
      [{ page: 1.5 }],
      [{ per_page: 2.5 }],
    ])("listVersions should reject invalid paging %j locally", async (params) => {
      await expect(service.listVersions("wf-123", params)).rejects.toThrow();

      expect(apiHandler.get).not.toHaveBeenCalled();
    });

    it("listVersions should pass through revisions without revision_index", async () => {
      // Backends that predate paging return history entries without revision_index.
      const response: WorkflowVersionHistoryResponse = {
        workflow_id: "wf-123",
        workflow_name: "My Workflow",
        total_revisions: 1,
        revisions: [
          {
            yaml_config: "steps: []",
            date: "2026-08-27T10:00:00",
            created_by: null,
            change_notes: null,
          },
        ],
      };

      apiHandler.get.mockResolvedValue(response);

      const result = await service.listVersions("wf-123");

      expect(result.revisions[0].revision_index).toBeUndefined();
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
});
