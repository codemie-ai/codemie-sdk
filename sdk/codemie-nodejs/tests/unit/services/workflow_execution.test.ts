import { jest, describe, expect, it, beforeEach } from "@jest/globals";
import { WorkflowExecutionService } from "../../../src/services/workflow_execution";
import { ApiRequestHandler } from "../../../src/utils/http";
import { PaginatedResponse } from "../../../src/models/common";
import {
  ExecutionStatus,
  ExecutionStatusType,
  WorkflowExecutionResponse,
} from "../../../src/models/workflow";
import { WorkflowExecutionStateService } from "../../../src/services/workflow_execution_state";
import { ApiError, NotFoundError } from "../../../src/exceptions";
import { omitKeys } from "../helpers";

jest.mock("../../../src/utils/http", () => ({
  ApiRequestHandler: jest.fn(),
}));

describe("WorkflowExecutionService", () => {
  const domain = "https://api.example.com";
  const token = "test-token";
  const workflowId = "123";
  let apiHandler: jest.Mocked<ApiRequestHandler>;
  let service: WorkflowExecutionService;

  const mockExecution: WorkflowExecutionResponse = {
    id: "1",
    execution_id: "exec-1",
    workflow_id: workflowId,
    overall_status: ExecutionStatus.SUCCEEDED as ExecutionStatusType,
    date: "2023-01-01",
    prompt: "test prompt",
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
    service = new WorkflowExecutionService(apiHandler, workflowId);
  });

  describe("list", () => {
    const createMockResponse = (
      data: WorkflowExecutionResponse[],
    ): PaginatedResponse<WorkflowExecutionResponse> => ({
      data,
      pagination: {
        total: data.length,
        page: 0,
        per_page: 10,
        pages: Math.ceil(data.length / 10),
      },
    });

    it("should list workflow executions with default parameters", async () => {
      const mockResponse = createMockResponse([mockExecution]);
      apiHandler.get.mockResolvedValue(mockResponse);

      const result = await service.list();

      expect(apiHandler.get).toHaveBeenCalledWith(`/v1/workflows/${workflowId}/executions`, {
        page: 0,
        per_page: 10,
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockExecution, ["date"]),
          created_date: mockExecution.date,
          overall_status: mockExecution.overall_status,
        },
      ]);
    });

    it("should list workflow executions with custom parameters", async () => {
      const mockExecutions = [mockExecution, { ...mockExecution, id: "2" }];
      const mockResponse = createMockResponse(mockExecutions);
      apiHandler.get.mockResolvedValue(mockResponse);

      const result = await service.list({
        page: 1,
        per_page: 20,
      });

      expect(apiHandler.get).toHaveBeenCalledWith(`/v1/workflows/${workflowId}/executions`, {
        page: 1,
        per_page: 20,
      });
      expect(result).toEqual([
        {
          ...omitKeys(mockExecutions[0], ["date"]),
          created_date: mockExecutions[0].date,
          overall_status: mockExecutions[0].overall_status,
        },
        {
          ...omitKeys(mockExecutions[1], ["date"]),
          created_date: mockExecutions[1].date,
          overall_status: mockExecutions[1].overall_status,
        },
      ]);
    });

    it("should handle empty execution list", async () => {
      const mockResponse = createMockResponse([]);
      apiHandler.get.mockResolvedValue(mockResponse);
      const result = await service.list();
      expect(result).toEqual([]);
    });

    it("should handle API errors", async () => {
      const error = new ApiError("Failed to fetch executions");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.list()).rejects.toThrow(error);
    });
  });

  describe("create", () => {
    const mockResponse = {
      execution_id: "exec-1",
      status: ExecutionStatus.IN_PROGRESS as ExecutionStatusType,
    };

    it("should create a new workflow execution with user input", async () => {
      apiHandler.post.mockResolvedValue(mockResponse);
      const result = await service.create("test input");

      expect(apiHandler.post).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions`,
        {
          user_input: "test input",
          file_name: undefined,
          propagate_headers: undefined,
        },
        {},
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should send attributes in the request body", async () => {
      apiHandler.post.mockResolvedValue(mockResponse);
      await service.create("x", undefined, undefined, undefined, undefined, undefined, {
        team: "alpha",
      });

      const body = apiHandler.post.mock.calls[0][1] as Record<string, unknown>;
      expect(body.attributes).toEqual({ team: "alpha" });
    });

    it("should leave attributes undefined (dropped by JSON) when omitted", async () => {
      apiHandler.post.mockResolvedValue(mockResponse);
      await service.create("x");

      const body = apiHandler.post.mock.calls[0][1] as Record<string, unknown>;
      expect(body.attributes).toBeUndefined();
    });

    it("should create a new workflow execution without user input", async () => {
      apiHandler.post.mockResolvedValue(mockResponse);
      const result = await service.create();

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

    it("should create a workflow execution with tags", async () => {
      apiHandler.post.mockResolvedValue(mockResponse);
      const tags = ["experiment", "sdk-test"];
      const result = await service.create(
        "test input",
        undefined,
        undefined,
        undefined,
        undefined,
        tags,
      );

      expect(apiHandler.post).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions`,
        {
          user_input: "test input",
          file_name: undefined,
          propagate_headers: undefined,
          tags,
        },
        {},
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during creation", async () => {
      const error = new ApiError("Creation failed");
      apiHandler.post.mockRejectedValue(error);
      await expect(service.create()).rejects.toThrow(error);
    });
  });

  describe("get", () => {
    it("should get workflow execution by ID", async () => {
      apiHandler.get.mockResolvedValue(mockExecution);
      const result = await service.get("exec-1");

      expect(apiHandler.get).toHaveBeenCalledWith(`/v1/workflows/${workflowId}/executions/exec-1`);
      expect(result).toEqual({
        ...omitKeys(mockExecution, ["date"]),
        created_date: mockExecution.date,
        overall_status: mockExecution.overall_status,
      });
    });

    it("should handle not found error", async () => {
      const error = new NotFoundError("WorkflowExecution", "exec-1");
      apiHandler.get.mockRejectedValue(error);
      await expect(service.get("exec-1")).rejects.toThrow(error);
    });
  });

  describe("states", () => {
    it("should return a workflow execution state service instance", () => {
      const stateService = service.states("exec-1");
      expect(stateService).toBeInstanceOf(WorkflowExecutionStateService);
    });

    it("should pass correct parameters to state service", () => {
      const stateService = service.states("exec-1");
      expect(stateService).toHaveProperty("workflowId", workflowId);
      expect(stateService).toHaveProperty("executionId", "exec-1");
    });
  });

  describe("deleteAll", () => {
    it("should delete all workflow executions", async () => {
      const mockResponse = { success: true };
      apiHandler.delete.mockResolvedValue(mockResponse);

      const result = await service.deleteAll();

      expect(apiHandler.delete).toHaveBeenCalledWith(`/v1/workflows/${workflowId}/executions`);
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during deletion", async () => {
      const error = new ApiError("Deletion failed");
      apiHandler.delete.mockRejectedValue(error);
      await expect(service.deleteAll()).rejects.toThrow(error);
    });
  });

  describe("abort", () => {
    it("should abort a running workflow execution", async () => {
      const mockResponse = { success: true };
      apiHandler.put.mockResolvedValue(mockResponse);

      const result = await service.abort("exec-1");

      expect(apiHandler.put).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions/exec-1/abort`,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during abort", async () => {
      const error = new ApiError("Abort failed");
      apiHandler.put.mockRejectedValue(error);
      await expect(service.abort("exec-1")).rejects.toThrow(error);
    });
  });

  describe("resume", () => {
    it("should resume an interrupted workflow execution", async () => {
      const mockResponse = { success: true };
      apiHandler.put.mockResolvedValue(mockResponse);

      const result = await service.resume("exec-1");

      expect(apiHandler.put).toHaveBeenCalledWith(
        `/v1/workflows/${workflowId}/executions/exec-1/resume`,
        {},
        { params: { propagate_headers: undefined } },
        undefined,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle API errors during resume", async () => {
      const error = new ApiError("Resume failed");
      apiHandler.put.mockRejectedValue(error);
      await expect(service.resume("exec-1")).rejects.toThrow(error);
    });
  });
});
