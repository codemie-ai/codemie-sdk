import type {
  Workflow,
  WorkflowExecution,
  WorkflowExecutionResponse,
  WorkflowResponse,
} from "../models";
import { omitUndefined } from "../utils/helpers";

export class WorkflowMapper {
  static mapWorkflowResponse(response: WorkflowResponse): Workflow {
    return omitUndefined({
      id: response.id,
      project: response.project,
      name: response.name,
      description: response.description,
      yaml_config: response.yaml_config,
      mode: response.mode,
      shared: response.shared,
      icon_url: response.icon_url,
      created_date: response.date,
      update_date: response.update_date,
      created_by: response.created_by,
    });
  }

  static mapWorkflowExecutionResponse(response: WorkflowExecutionResponse): WorkflowExecution {
    return omitUndefined({
      id: response.id,
      execution_id: response.execution_id,
      workflow_id: response.workflow_id,
      overall_status: response.overall_status,
      created_date: response.date,
      prompt: response.prompt,
      updated_date: response.updated_date,
      created_by: response.created_by,
      tokens_usage: response.tokens_usage,
      attributes: response.attributes,
    });
  }
}
