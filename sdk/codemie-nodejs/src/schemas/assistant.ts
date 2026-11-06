import { z } from "zod";

export const AssistantListParamsSchema = z
  .object({
    minimal_response: z.boolean().default(true),
    scope: z.enum(["visible_to_user", "marketplace"]).default("visible_to_user"),
    page: z.number().default(0),
    per_page: z.number().default(12),
    filters: z.record(z.string(), z.unknown()).optional(),
  })
  .readonly();
export type AssistantListParams = Partial<z.infer<typeof AssistantListParamsSchema>>;

const PromptVariableSchema = z.object({
  key: z.string().max(100),
  description: z.string().max(200).optional().nullable(),
  default_value: z.string().max(500).optional(),
});

// The API echoes an inline config with its unused keys set to null - a stdio server
// comes back carrying `url: null`, a remote one `command: null` - so every key here
// accepts null, the way the virtual-assistant config schema already does.
const MCPServerConfigObjectSchema = z.looseObject({
  url: z.string().optional().nullable(),
  command: z.string().optional().nullable(),
  args: z.array(z.string()).optional().nullable(),
  env: z.record(z.string(), z.unknown()).optional().nullable(),
  auth_token: z.string().optional().nullable(),
  headers: z.record(z.string(), z.string()).optional().nullable(),
  type: z.string().optional().nullable(),
  single_usage: z.boolean().optional().nullable(),
  audience: z.string().optional().nullable(),
  tools: z.array(z.string()).optional().nullable(),
});

export const MCPServerConfigSchema = MCPServerConfigObjectSchema.optional()
  .nullable()
  .refine((config) => {
    if (!config || Object.keys(config).length === 0) {
      return true;
    }
    const hasUrl = !!config.url?.trim();
    const hasCommand = !!config.command?.trim();
    return hasUrl !== hasCommand;
  }, "Either 'url' or 'command' must be provided in config, but not both");

const AssistantParamsFields = {
  name: z.string(),
  description: z.string().optional().nullable(),
  icon_url: z.string().optional().nullable(),
  system_prompt: z.string(),
  project: z.string().optional(),
  context: z
    .array(
      z.object({
        context_type: z.enum(["knowledge_base", "code", "provider"]),
        name: z.string(),
      }),
    )
    .optional(),
  llm_model_type: z.string(),
  toolkits: z
    .array(
      z.object({
        toolkit: z.string(),
        tools: z.array(
          z.object({
            name: z.string(),
            label: z.string().optional().nullable(),
            settings_config: z.boolean().optional(),
            user_description: z.string().optional().nullable(),
            settings: z.any().nullable().optional(),
          }),
        ),
        label: z.string().optional(),
        settings_config: z.boolean().optional(),
        is_external: z.boolean().optional().nullable(),
        settings: z.any().optional(),
      }),
    )
    .optional(),
  conversation_starters: z.array(z.string()).optional(),
  shared: z.boolean().optional(),
  is_react: z.boolean().optional(),
  is_global: z.boolean().optional().nullable(),
  slug: z.string().optional().nullable(),
  temperature: z.number().optional().nullable(),
  top_p: z.number().optional().nullable(),
  mcp_servers: z
    .array(
      z.looseObject({
        name: z.string(),
        description: z.string().optional().nullable(),
        enabled: z.boolean().optional(),
        config: MCPServerConfigSchema,
        mcp_connect_url: z.string().optional().nullable(),
        tools_tokens_size_limit: z.number().int().optional().nullable(),
        command: z.string().optional().nullable(),
        arguments: z.string().optional().nullable(),
        settings: z.any().optional(),
        mcp_connect_auth_token: z.any().optional(),
        mcp_config_id: z.string().optional().nullable(),
        integration_alias: z.string().optional().nullable(),
        use_custom_config: z.boolean().optional(),
        resolve_dynamic_values_in_arguments: z.boolean().optional(),
        tools: z.array(z.string()).optional().nullable(),
      }),
    )
    .optional(),
  assistant_ids: z.array(z.string()).optional(),
  skill_ids: z.array(z.string()).optional(),
  prompt_variables: z.array(PromptVariableSchema).nullable().optional(),
  categories: z
    .array(z.union([z.string(), z.looseObject({ id: z.string() })]))
    .max(3)
    .optional(),
  skip_integration_validation: z.boolean().optional().nullable(),
};

export const AssistantCreateParamsSchema = z
  .object({
    ...AssistantParamsFields,
    prompt_variables: AssistantParamsFields.prompt_variables.default([]),
    skip_integration_validation: AssistantParamsFields.skip_integration_validation.default(false),
  })
  .readonly();
// In order to make sure that default values are applied correctly, we use z.input here
// instead of z.infer which would give us the type after defaults are applied.
export type AssistantCreateParams = z.input<typeof AssistantCreateParamsSchema>;

export const AssistantUpdateParamsSchema = z.object(AssistantParamsFields).readonly();
export type AssistantUpdateParams = z.input<typeof AssistantUpdateParamsSchema>;

export const AssistantChatParamsSchema = z
  .object({
    conversation_id: z.string().optional(),
    text: z.string(),
    content_raw: z.string().optional(),
    file_names: z.array(z.string()).optional(),
    llm_model: z.string().optional(),
    history: z.union([
      z.array(
        z.object({
          role: z.enum(["Assistant", "User"]),
          message: z.string().optional(),
        }),
      ),
      z.string(),
    ]),
    history_index: z.number().optional(),
    stream: z.boolean().optional(),
    propagate_headers: z.boolean().optional(),
    custom_metadata: z.record(z.string(), z.unknown()).optional(),
    top_k: z.number().optional(),
    system_prompt: z.string().optional(),
    background_task: z.boolean().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    mcp_server_single_usage: z.boolean().optional(),
    save_history: z.boolean().optional(),

    version: z.number().optional(),
    output_schema: z
      .union([z.custom((val) => val instanceof z.ZodType), z.record(z.string(), z.unknown())])
      .optional(),
  })
  .readonly();
export type AssistantChatParams = z.infer<typeof AssistantChatParamsSchema>;

const VirtualAssistantContextSchema = z.object({
  context_type: z.enum(["knowledge_base", "code", "provider"]),
  name: z.string(),
});

const VirtualAssistantToolSchema = z.object({
  name: z.string(),
  label: z.string().nullable().optional(),
  settings_config: z.boolean(),
  user_description: z.string().nullable().optional(),
  settings: z.any().nullable().optional(),
});

const VirtualAssistantToolKitSchema = z.object({
  toolkit: z.string(),
  tools: z.array(VirtualAssistantToolSchema),
  label: z.string(),
  settings_config: z.boolean(),
  is_external: z.boolean().nullable().optional(),
  settings: z.any().optional(),
});

const VirtualAssistantMCPServerConfigSchema = z.looseObject({
  command: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
  args: z.array(z.string()).nullable().optional(),
  env: z.record(z.string(), z.unknown()).nullable().optional(),
  auth_token: z.string().nullable().optional(),
  headers: z.record(z.string(), z.string()).nullable().optional(),
  type: z.string().nullable().optional(),
  single_usage: z.boolean().nullable().optional(),
  audience: z.string().nullable().optional(),
  auth_config: z.record(z.string(), z.unknown()).nullable().optional(),
  tools: z.array(z.string()).nullable().optional(),
});

const VirtualAssistantMCPServerSchema = z.looseObject({
  name: z.string(),
  description: z.string().nullable().optional(),
  enabled: z.boolean(),
  config: VirtualAssistantMCPServerConfigSchema.nullable().optional(),
  mcp_connect_url: z.string().nullable().optional(),
  tools_tokens_size_limit: z.number().nullable().optional(),
  command: z.string().nullable().optional(),
  arguments: z.string().nullable().optional(),
  settings: z.any().optional(),
  mcp_connect_auth_token: z.any().optional(),
  mcp_config_id: z.string().nullable().optional(),
  integration_alias: z.string().nullable().optional(),
  use_custom_config: z.boolean().nullable().optional(),
  resolve_dynamic_values_in_arguments: z.boolean().nullable().optional(),
  tools: z.array(z.string()).nullable().optional(),
});

export const VirtualAssistantChatParamsSchema = z
  .object({
    // Assistant definition fields
    system_prompt: z.string().default(""),
    llm_model_type: z.string().optional(),
    temperature: z.number().min(0).max(2).optional(),
    top_p: z.number().min(0).max(1).optional(),
    toolkits: z.array(VirtualAssistantToolKitSchema).default([]),
    context: z.array(VirtualAssistantContextSchema).default([]),
    mcp_servers: z.array(VirtualAssistantMCPServerSchema).default([]),
    skill_ids: z.array(z.string()).default([]),
    assistant_ids: z.array(z.string()).default([]),
    agent_mode: z.enum(["general", "plan_execute"]).default("general"),
    plan_prompt: z.string().optional(),
    smart_tool_selection_enabled: z.boolean().default(false),
    prompt_variables: z.array(PromptVariableSchema).default([]),

    // Chat parameters
    conversation_id: z.string().optional(),
    text: z.string(),
    content_raw: z.string().optional(),
    file_names: z.array(z.string()).optional(),
    history: z
      .union([
        z.array(
          z.object({
            role: z.enum(["Assistant", "User"]),
            message: z.string().optional(),
          }),
        ),
        z.string(),
      ])
      .default([]),
    stream: z.boolean().optional(),
    output_schema: z
      .union([z.custom((val) => val instanceof z.ZodType), z.record(z.string(), z.unknown())])
      .optional(),
    tools_config: z
      .array(
        z.object({
          name: z.string(),
          tool_creds: z.record(z.string(), z.unknown()).optional(),
          integration_id: z.string().optional(),
        }),
      )
      .optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    top_k: z.number().default(10),
    propagate_headers: z.boolean().default(false),
    disable_cache: z.boolean().optional(),
    mcp_server_single_usage: z.boolean().optional(),
  })
  .readonly();
export type VirtualAssistantChatParams = z.input<typeof VirtualAssistantChatParamsSchema>;

export const AssistantEvaluationParamsSchema = z
  .object({
    dataset_id: z.string(),
    experiment_name: z.string(),
    system_prompt: z.string().optional(),
    llm_model: z.string().optional(),
  })
  .readonly();
export type AssistantEvaluationParams = z.infer<typeof AssistantEvaluationParamsSchema>;

export const AssistantVersionsListParamsSchema = z
  .object({
    page: z.number().optional(),
    per_page: z.number().optional(),
  })
  .readonly();
export type AssistantVersionsListParams = Partial<
  z.infer<typeof AssistantVersionsListParamsSchema>
>;
