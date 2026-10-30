/** Models for assistant-related data structures. */

import type { BaseUser } from "./common";
import type { Integration } from "./integration";
import type { AgentErrorDetails, ToolErrorDetails } from "./errors";

export enum ContextType {
  KNOWLEDGE_BASE = "knowledge_base",
  CODE = "code",
  PROVIDER = "provider",
}

export enum ChatRole {
  ASSISTANT = "Assistant",
  USER = "User",
}

export interface ToolDetails {
  description?: string | null;
  label?: string;
  name: string;
  settings?: Integration | null;
  settings_config: boolean;
  user_description?: string;
}

export interface ToolKitDetails {
  is_external: boolean;
  label: string;
  settings?: Integration;
  settings_config: boolean;
  toolkit: string;
  tools: ToolDetails[];
}

export interface Context {
  context_type: ContextType;
  name: string;
}

export interface PromptVariable {
  key: string;
  description?: string;
  default_value: string;
}

export interface MCPServerConfig {
  command?: string | null;
  url?: string | null;
  args?: string[] | null;
  env?: Record<string, unknown> | null;
  headers?: Record<string, string> | null;
  type?: string | null;
  auth_token?: string | null;
  single_usage?: boolean | null;
  audience?: string | null;
  tools?: string[] | null;
}

export interface MCPServerDetails {
  name: string;
  description?: string | null;
  enabled: boolean;
  config?: MCPServerConfig | null;
  mcp_connect_url?: string;
  tools_tokens_size_limit?: number;
  command?: string;
  arguments?: string;
  settings?: Integration;
  mcp_connect_auth_token?: Integration;
  mcp_config_id?: string | null;
  integration_alias?: string | null;
  use_custom_config?: boolean | null;
  resolve_dynamic_values_in_arguments?: boolean | null;
  tools?: string[] | null;
}

export interface SystemPromptHistory {
  system_prompt: string;
  date: string;
  created_by?: BaseUser;
}

export interface AssistantCategory {
  id: string;
  name: string;
  description?: string;
}

export interface AssistantBase {
  id: string;
  created_by?: BaseUser;
  description: string;
  icon_url?: string;
  name: string;
}

export interface Assistant extends AssistantBase {
  display_name?: string | null;
  assistant_ids: string[];
  categories?: AssistantCategory[];
  context: Context[];
  deselected_default_tools: string[];
  skill_ids?: string[];
  conversation_starters: string[];
  created_date?: string;
  creator: string;
  is_global: boolean;
  is_react: boolean;
  llm_model_type?: string;
  mcp_servers: MCPServerDetails[];
  nested_assistants: Partial<Assistant>[];
  project: string;
  prompt_variables?: PromptVariable[];
  shared: boolean;
  slug?: string;
  system_prompt: string;
  system_prompt_history: SystemPromptHistory[];
  temperature?: number;
  toolkits: ToolKitDetails[];
  top_p?: number;
  unique_users_count?: number;
  updated_date?: string;
  user_abilities?: unknown[];
  version_count?: number;
}

/**
 * API response for assistant chat (camelCase format from API).
 *
 * Error fields expose agent and tool errors.
 */
export interface BaseModelApiResponse {
  generated: string;
  timeElapsed?: number;
  tokensUsed?: number;
  thoughts?: Record<string, unknown>[];
  taskId?: string;
  success?: boolean;
  agentError?: AgentErrorDetails;
  toolErrors?: ToolErrorDetails[];
}

/**
 * Client-facing response for assistant chat (snake_case format).
 *
 * Error fields expose agent and tool errors without breaking backward
 * compatibility (all error fields optional).
 */
export interface BaseModelResponse {
  generated: string | object | unknown;
  time_elapsed?: number;
  tokens_used?: number;
  thoughts?: Record<string, unknown>[];
  task_id?: string;
  success?: boolean;
  agent_error?: AgentErrorDetails;
  tool_errors?: ToolErrorDetails[];
}

// Assistant versioning models
export interface AssistantVersion {
  version_number: number;
  created_date: string;
  created_by?: BaseUser;
  change_notes?: string;
  description?: string;
  system_prompt: string;
  llm_model_type?: string;
  temperature?: number;
  top_p?: number;
  context: Context[];
  toolkits: ToolKitDetails[];
  mcp_servers: MCPServerDetails[];
  assistant_ids: string[];
  prompt_variables?: PromptVariable[];
  deselected_default_tools: string[];
  // allow future fields without breaking consumers
  [key: string]: unknown;
}

// Assistant validation models
export interface MissingIntegration {
  toolkit: string;
  tool: string;
  label: string;
  credential_type?: string;
}

export interface MissingIntegrationsByCredentialType {
  credential_type: string;
  missing_tools: MissingIntegration[];
  assistant_id?: string;
  assistant_name?: string;
  icon_url?: string;
}

export interface IntegrationValidationResult {
  has_missing_integrations: boolean;
  missing_by_credential_type: MissingIntegrationsByCredentialType[];
  sub_assistants_missing: MissingIntegrationsByCredentialType[];
  message?: string;
}

export interface AssistantCreateResponse {
  message: string;
  assistant_id?: string;
  validation?: IntegrationValidationResult;
}

export interface AssistantUpdateResponse {
  message: string;
  validation?: IntegrationValidationResult;
}

// Note: compareVersions returns a generic object; no strict SDK interface is defined
