/** Models for workflow functionality */
import type { BaseUser, TokensUsage } from "./common";

/** Available workflow modes */
export const WorkflowMode = {
  SEQUENTIAL: "Sequential",
  AUTONOMOUS: "Autonomous",
} as const;
export type WorkflowModeType = (typeof WorkflowMode)[keyof typeof WorkflowMode];

/** Workflow execution status */
export const ExecutionStatus = {
  IN_PROGRESS: "In Progress",
  NOT_STARTED: "Not Started",
  INTERRUPTED: "Interrupted",
  FAILED: "Failed",
  SUCCEEDED: "Succeeded",
  ABORTED: "Aborted",
} as const;
export type ExecutionStatusType = (typeof ExecutionStatus)[keyof typeof ExecutionStatus];

/** Workflow API response */
export interface WorkflowResponse {
  /** Unique identifier */
  id: string;
  /** Project name */
  project: string;
  /** Workflow name */
  name: string;
  /** Workflow description */
  description?: string;
  /** YAML configuration */
  yaml_config?: string;
  /** Workflow execution mode */
  mode: WorkflowModeType;
  /** Whether workflow is shared */
  shared: boolean;
  /** URL to workflow icon */
  icon_url?: string;
  /** Creation date */
  date: string;
  /** Last update date */
  update_date: string;
  /** Creator information */
  created_by: BaseUser;
}

/** Workflow model */
export interface Workflow {
  /** Unique identifier */
  id: string;
  /** Project name */
  project: string;
  /** Workflow name */
  name: string;
  /** Workflow description */
  description?: string;
  /** YAML configuration */
  yaml_config?: string;
  /** Workflow execution mode */
  mode: WorkflowModeType;
  /** Whether workflow is shared */
  shared: boolean;
  /** URL to workflow icon */
  icon_url?: string;
  /** Creation date */
  created_date: string;
  /** Last update date */
  update_date: string;
  /** Creator information */
  created_by: BaseUser;
  /** Project display name, populated at response time */
  display_name?: string | null;
}

/** Workflow execution API response */
export interface WorkflowExecutionResponse {
  /** Unique identifier */
  id: string;
  /** Execution identifier */
  execution_id: string;
  /** Associated workflow identifier */
  workflow_id: string;
  /** Execution status */
  overall_status: ExecutionStatusType;
  /** Creation date */
  date: string;
  /** Execution prompt */
  prompt: string;
  /** Last update date */
  updated_date?: string;
  /** Creator information */
  created_by: BaseUser;
  /** Token usage statistics */
  tokens_usage?: TokensUsage;
}

/** Model representing a workflow execution */
export interface WorkflowExecution {
  /** Unique identifier */
  id: string;
  /** Execution identifier */
  execution_id: string;
  /** Associated workflow identifier */
  workflow_id: string;
  /** Execution status */
  overall_status: ExecutionStatusType;
  /** Creation date */
  created_date: string;
  /** Execution prompt */
  prompt: string;
  /** Last update date */
  updated_date?: string;
  /** Creator information */
  created_by: BaseUser;
  /** Token usage statistics */
  tokens_usage?: TokensUsage;
}

/** Model for workflow execution state thought */
export interface WorkflowExecutionStateThought {
  /** Unique identifier */
  id: string;
  /** Thought content */
  text: string;
  /** Creation timestamp */
  created_at: string;
  /** Parent thought identifier */
  parent_id?: string;
}

/** Model for workflow execution state */
export interface WorkflowExecutionState {
  /** Unique identifier */
  id: string;
  /** Execution identifier */
  execution_id: string;
  /** State name */
  name: string;
  /** Associated task */
  task?: string;
  /** State status */
  status: ExecutionStatusType;
  /** Start timestamp */
  started_at?: string;
  /** Completion timestamp */
  completed_at?: string;
}

/** Model for workflow execution state output */
export interface WorkflowExecutionStateOutput {
  /** Output content */
  output?: string;
}

/** Creator information on a workflow revision (backend UserEntity: keyed by `user_id`, not `id`). */
export interface WorkflowRevisionCreatedBy {
  user_id: string;
  username: string;
  name: string;
}

/** A single workflow revision entry */
export interface WorkflowRevision {
  /** Full YAML config snapshot */
  yaml_config: string;
  /** ISO-8601 timestamp of this revision */
  date: string;
  /** User who created this revision; null when the backend has no creator recorded */
  created_by: WorkflowRevisionCreatedBy | null;
  /** Optional audit note */
  change_notes: string | null;
}

/** Response for GET /v1/workflows/{id}/versions */
export interface WorkflowVersionHistoryResponse {
  workflow_id: string;
  workflow_name: string;
  total_revisions: number;
  revisions: WorkflowRevision[];
}
