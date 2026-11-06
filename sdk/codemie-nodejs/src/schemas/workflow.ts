import { z } from "zod";
import { WorkflowMode } from "../models/workflow";

/**
 * Workflow list parameters schema
 */
export const WorkflowListParamsSchema = z
  .object({
    page: z.number().default(0),
    per_page: z.number().default(10),
    projects: z.array(z.string()).optional(),
    search: z.string().optional(),
  })
  .readonly();
export type WorkflowListParams = Partial<z.infer<typeof WorkflowListParamsSchema>>;

/**
 * Workflow create parameters schema
 */
export const WorkflowCreateParamsSchema = z
  .object({
    project: z.string(),
    name: z.string(),
    description: z.string().optional(),
    yaml_config: z.string(),
    mode: z.enum([WorkflowMode.SEQUENTIAL, WorkflowMode.AUTONOMOUS]),
    shared: z.boolean(),
    icon_url: z.string().optional(),
  })
  .readonly();
export type WorkflowCreateParams = z.infer<typeof WorkflowCreateParamsSchema>;

/**
 * Workflow update parameters schema
 */
export const WorkflowUpdateParamsSchema = z
  .object({
    project: z.string(),
    name: z.string(),
    description: z.string().optional(),
    yaml_config: z.string(),
    mode: z.enum([WorkflowMode.SEQUENTIAL, WorkflowMode.AUTONOMOUS]).optional(),
    shared: z.boolean().optional(),
    icon_url: z.string().optional(),
  })
  .readonly();
export type WorkflowUpdateParams = z.infer<typeof WorkflowUpdateParamsSchema>;

/**
 * Workflow evaluation parameters schema
 */
export const WorkflowEvaluationParamsSchema = z
  .object({
    dataset_id: z.string(),
    experiment_name: z.string(),
    max_concurrency: z.number().min(1).max(5).default(1),
  })
  .readonly();
export type WorkflowEvaluationParams = z.infer<typeof WorkflowEvaluationParamsSchema>;

/**
 * Workflow execution list parameters schema
 */
export const WorkflowExecutionListParamsSchema = z
  .object({
    page: z.number().default(0),
    per_page: z.number().default(10),
  })
  .readonly();
export type WorkflowExecutionListParams = Partial<
  z.infer<typeof WorkflowExecutionListParamsSchema>
>;

/**
 * Workflow execution create parameters schema
 */
export const WorkflowExecutionCreateParamsSchema = z
  .object({
    user_input: z
      .union([
        z.string(),
        z.record(z.string(), z.unknown()),
        z.array(z.unknown()),
        z.number(),
        z.boolean(),
      ])
      .optional(),
    file_name: z.string().optional(),
    session_id: z.string().optional(),
    propagate_headers: z.boolean().optional(),
    tags: z.array(z.string()).optional(),
  })
  .readonly();
export type WorkflowExecutionCreateParams = z.infer<typeof WorkflowExecutionCreateParamsSchema>;

/**
 * Workflow execution state list parameters schema
 */
export const WorkflowExecutionStateListParamsSchema = z
  .object({
    page: z.number().default(0),
    per_page: z.number().default(10),
  })
  .readonly();
export type WorkflowExecutionStateListParams = Partial<
  z.infer<typeof WorkflowExecutionStateListParamsSchema>
>;

/**
 * Workflow rollback parameters schema
 */
export const WorkflowRollbackParamsSchema = z
  .object({
    revision_index: z.number().int().min(0),
    change_notes: z.string().optional(),
  })
  .readonly();
export type WorkflowRollbackParams = z.infer<typeof WorkflowRollbackParamsSchema>;
