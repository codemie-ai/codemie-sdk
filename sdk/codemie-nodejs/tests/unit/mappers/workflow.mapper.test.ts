import { describe, it, expect } from "@jest/globals";
import { WorkflowMapper } from "../../../src/mappers/workflow.mapper";
import type {
  ExecutionStatusType,
  WorkflowExecutionResponse,
  WorkflowExecutionState,
  WorkflowResponse,
} from "../../../src/models";
import { WorkflowMode, ExecutionStatus } from "../../../src/models/workflow";

describe("WorkflowMapper", () => {
  describe("mapWorkflowResponse", () => {
    it("should correctly map all workflow fields", () => {
      // Arrange
      const apiResponse: WorkflowResponse = {
        id: "workflow-123",
        project: "project-1",
        name: "Test Workflow",
        description: "A test workflow",
        yaml_config: "config: test",
        mode: WorkflowMode.SEQUENTIAL,
        shared: true,
        icon_url: "https://example.com/icon.png",
        date: "2025-01-01",
        update_date: "2025-01-02",
        created_by: {
          username: "user1",
          name: "User One",
        },
      };

      // Act
      const result = WorkflowMapper.mapWorkflowResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "workflow-123",
        project: "project-1",
        name: "Test Workflow",
        description: "A test workflow",
        yaml_config: "config: test",
        mode: WorkflowMode.SEQUENTIAL,
        shared: true,
        icon_url: "https://example.com/icon.png",
        created_date: "2025-01-01",
        update_date: "2025-01-02",
        created_by: {
          username: "user1",
          name: "User One",
        },
      });
    });

    it("should handle empty values", () => {
      // Arrange
      const apiResponse: WorkflowResponse = {
        id: "workflow-123",
        project: "project-1",
        name: "",
        description: "",
        yaml_config: "",
        mode: WorkflowMode.SEQUENTIAL,
        shared: false,
        icon_url: "",
        date: "",
        update_date: "",
        created_by: {
          username: "user1",
          name: "User One",
        },
      };

      // Act
      const result = WorkflowMapper.mapWorkflowResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "workflow-123",
        project: "project-1",
        name: "",
        description: "",
        yaml_config: "",
        mode: WorkflowMode.SEQUENTIAL,
        shared: false,
        icon_url: "",
        created_date: "",
        update_date: "",
        created_by: {
          username: "user1",
          name: "User One",
        },
      });
    });
  });

  describe("mapWorkflowExecutionResponse", () => {
    const responseForStatus = (status: ExecutionStatusType): WorkflowExecutionResponse => ({
      id: "exec-123",
      execution_id: "execution-123",
      workflow_id: "workflow-123",
      overall_status: status,
      date: "2025-01-01",
      prompt: "test prompt",
      created_by: { username: "user1", name: "User One" },
    });

    it.each<[keyof typeof ExecutionStatus, ExecutionStatusType]>([
      ["IN_PROGRESS", "In Progress"],
      ["NOT_STARTED", "Not Started"],
      ["INTERRUPTED", "Interrupted"],
      ["FAILED", "Failed"],
      ["SUCCEEDED", "Succeeded"],
      ["ABORTED", "Aborted"],
    ])("preserves legacy %s status", (member, wireValue) => {
      expect(ExecutionStatus[member]).toBe(wireValue);
      const result = WorkflowMapper.mapWorkflowExecutionResponse(responseForStatus(wireValue));
      expect(result.overall_status).toBe(wireValue);
    });

    it.each<["RECOVERING" | "NEEDS_TRIAGE" | "AUTHENTICATION_REQUIRED", ExecutionStatusType]>([
      ["RECOVERING", ExecutionStatus.RECOVERING],
      ["NEEDS_TRIAGE", ExecutionStatus.NEEDS_TRIAGE],
      ["AUTHENTICATION_REQUIRED", ExecutionStatus.AUTHENTICATION_REQUIRED],
    ])("exports and preserves %s status", (wireValue, constant) => {
      expect(constant).toBe(wireValue);
      const result = WorkflowMapper.mapWorkflowExecutionResponse(responseForStatus(wireValue));
      expect(result.overall_status).toBe(wireValue);
    });

    it("accepts new literal values in execution and state status types", () => {
      const executionStatuses: ExecutionStatusType[] = ["RECOVERING", "NEEDS_TRIAGE"];
      const stateStatuses: WorkflowExecutionState["status"][] = ["RECOVERING", "NEEDS_TRIAGE"];
      expect(executionStatuses).toEqual(["RECOVERING", "NEEDS_TRIAGE"]);
      expect(stateStatuses).toEqual(["RECOVERING", "NEEDS_TRIAGE"]);
    });

    it("passes an unknown server status through without validation", () => {
      const response = responseForStatus("FUTURE_STATUS" as ExecutionStatusType);
      expect(WorkflowMapper.mapWorkflowExecutionResponse(response).overall_status).toBe("FUTURE_STATUS");
    });

    it("should correctly map all execution fields", () => {
      // Arrange
      const apiResponse: WorkflowExecutionResponse = {
        id: "exec-123",
        execution_id: "execution-123",
        workflow_id: "workflow-123",
        overall_status: ExecutionStatus.SUCCEEDED,
        date: "2025-01-01",
        prompt: "test prompt",
        updated_date: "2025-01-02",
        created_by: {
          username: "user1",
          name: "User One",
        },
        tokens_usage: {
          input_tokens: 50,
          output_tokens: 50,
        },
      };

      // Act
      const result = WorkflowMapper.mapWorkflowExecutionResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "exec-123",
        execution_id: "execution-123",
        workflow_id: "workflow-123",
        overall_status: ExecutionStatus.SUCCEEDED,
        created_date: "2025-01-01",
        prompt: "test prompt",
        updated_date: "2025-01-02",
        created_by: {
          username: "user1",
          name: "User One",
        },
        tokens_usage: {
          input_tokens: 50,
          output_tokens: 50,
        },
      });
    });

    it("should handle empty values", () => {
      // Arrange
      const apiResponse: WorkflowExecutionResponse = {
        id: "exec-123",
        execution_id: "execution-123",
        workflow_id: "workflow-123",
        overall_status: ExecutionStatus.NOT_STARTED,
        date: "",
        prompt: "",
        updated_date: "",
        created_by: {
          username: "user1",
          name: "User One",
        },
        tokens_usage: {
          input_tokens: 0,
          output_tokens: 0,
        },
      };

      // Act
      const result = WorkflowMapper.mapWorkflowExecutionResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "exec-123",
        execution_id: "execution-123",
        workflow_id: "workflow-123",
        overall_status: ExecutionStatus.NOT_STARTED,
        created_date: "",
        prompt: "",
        updated_date: "",
        created_by: {
          username: "user1",
          name: "User One",
        },
        tokens_usage: {
          input_tokens: 0,
          output_tokens: 0,
        },
      });
    });
  });
});
