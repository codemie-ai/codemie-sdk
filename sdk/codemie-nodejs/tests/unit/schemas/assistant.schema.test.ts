import { describe, expect, it } from "@jest/globals";
import {
  AssistantCreateParamsSchema,
  AssistantUpdateParamsSchema,
  MCPServerConfigSchema,
  VirtualAssistantChatParamsSchema,
} from "../../../src/schemas/assistant";

describe("MCPServerConfigSchema", () => {
  it("accepts undefined", () => {
    expect(MCPServerConfigSchema.parse(undefined)).toBeUndefined();
  });

  it("accepts url-based config with headers, type, single_usage, and audience", () => {
    const parsed = MCPServerConfigSchema.parse({
      url: "https://mcp.example.com/mcp",
      headers: { Authorization: "Bearer token", "X-Custom": "1" },
      type: "streamable-http",
      single_usage: true,
      audience: "https://api.resource/.default",
    });
    expect(parsed).toEqual({
      url: "https://mcp.example.com/mcp",
      headers: { Authorization: "Bearer token", "X-Custom": "1" },
      type: "streamable-http",
      single_usage: true,
      audience: "https://api.resource/.default",
    });
  });

  it("accepts command-based config with optional fields", () => {
    const parsed = MCPServerConfigSchema.parse({
      command: "npx",
      args: ["-y", "some-mcp"],
      env: { FOO: "bar" },
      type: "stdio",
      single_usage: false,
    });
    expect(parsed?.command).toBe("npx");
    expect(parsed?.single_usage).toBe(false);
  });

  it("rejects both url and command in the same config", () => {
    expect(() =>
      MCPServerConfigSchema.parse({
        url: "https://a",
        command: "npx",
      }),
    ).toThrow();
  });
});

describe("AssistantCreateParamsSchema mcp_servers.config", () => {
  const base = {
    name: "A",
    description: "D",
    system_prompt: "P",
    project: "proj",
    context: [],
    llm_model_type: "gpt-4",
    toolkits: [],
    conversation_starters: [],
    assistant_ids: [],
    mcp_servers: [
      {
        name: "remote",
        enabled: true,
        config: {
          url: "https://mcp.example.com",
          headers: { "X-Api-Key": "k" },
          type: "streamable-http",
          single_usage: true,
          audience: "aud",
        },
      },
    ],
  };

  it("preserves extended mcp config fields on create params", () => {
    const parsed = AssistantCreateParamsSchema.parse(base);
    expect(parsed.mcp_servers[0].config).toEqual({
      url: "https://mcp.example.com",
      headers: { "X-Api-Key": "k" },
      type: "streamable-http",
      single_usage: true,
      audience: "aud",
    });
  });

  it("preserves streamable-http config headers, type, single_usage, and tools", () => {
    const parsed = AssistantCreateParamsSchema.parse({
      ...base,
      mcp_servers: [
        {
          name: "remote",
          enabled: true,
          config: {
            url: "https://mcp.example.com/mcp",
            headers: { Authorization: "Bearer token" },
            type: "streamable-http",
            single_usage: true,
            tools: ["tool-a"],
          },
        },
      ],
    });

    expect(parsed.mcp_servers[0].config).toEqual({
      url: "https://mcp.example.com/mcp",
      headers: { Authorization: "Bearer token" },
      type: "streamable-http",
      single_usage: true,
      tools: ["tool-a"],
    });
  });
});

describe("AssistantCreateParamsSchema mcp_servers pass-through", () => {
  const base = {
    name: "A",
    description: "D",
    system_prompt: "P",
    project: "proj",
    context: [],
    llm_model_type: "gpt-4",
    toolkits: [],
    conversation_starters: [],
    assistant_ids: [],
    mcp_servers: [
      {
        name: "remote",
        enabled: true,
        future_backend_field: "x",
        config: {
          url: "https://mcp.example.com",
          future_config_field: "y",
        },
      },
    ],
  };

  it("forwards an undeclared key on an mcp_servers item", () => {
    const parsed = AssistantCreateParamsSchema.parse(base);
    expect(parsed.mcp_servers[0]).toMatchObject({
      name: "remote",
      enabled: true,
      future_backend_field: "x",
    });
  });

  it("forwards an undeclared key inside mcp_servers[].config", () => {
    const parsed = AssistantCreateParamsSchema.parse(base);
    expect(parsed.mcp_servers[0].config).toMatchObject({
      url: "https://mcp.example.com",
      future_config_field: "y",
    });
  });

  // Loosening must only reach keys the schema does not declare; the declared ones stay validated.
  it("still rejects a wrong type on a declared mcp_servers field", () => {
    expect(() =>
      AssistantCreateParamsSchema.parse({
        ...base,
        mcp_servers: [{ name: "remote", enabled: "yes" }],
      }),
    ).toThrow();
  });

  it("still enforces the url-xor-command refine on a loosened item's config", () => {
    expect(() =>
      AssistantCreateParamsSchema.parse({
        ...base,
        mcp_servers: [
          { name: "remote", enabled: true, config: { url: "https://a", command: "npx" } },
        ],
      }),
    ).toThrow();
  });
});

describe("AssistantUpdateParamsSchema mcp_servers top-level fields", () => {
  it("accepts explicit null values for saved-config MCP fields", () => {
    const parsed = AssistantUpdateParamsSchema.parse({
      name: "a",
      description: "d",
      system_prompt: "x",
      project: "p",
      context: [],
      llm_model_type: "m",
      toolkits: [],
      conversation_starters: [],
      assistant_ids: [],
      mcp_servers: [
        {
          name: "RI-logs",
          description: "Download, unzip and grep log files",
          enabled: true,
          mcp_config_id: null,
          integration_alias: null,
          resolve_dynamic_values_in_arguments: null,
          tools: null,
          config: null,
        },
      ],
    });

    expect(parsed.mcp_servers[0]).toMatchObject({
      name: "RI-logs",
      description: "Download, unzip and grep log files",
      enabled: true,
      mcp_config_id: null,
      integration_alias: null,
      resolve_dynamic_values_in_arguments: null,
      tools: null,
      config: null,
    });
  });

  it("preserves saved-config MCP fields including mcp_config_id", () => {
    const parsed = AssistantUpdateParamsSchema.parse({
      name: "a",
      description: "d",
      system_prompt: "x",
      project: "p",
      context: [],
      llm_model_type: "m",
      toolkits: [],
      conversation_starters: [],
      assistant_ids: [],
      mcp_servers: [
        {
          name: "RI-logs",
          description: "Download, unzip and grep log files",
          enabled: true,
          mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
          integration_alias: "ri-logs-alias",
          resolve_dynamic_values_in_arguments: false,
          tools: ["fetch_logs", "grep_logs"],
        },
      ],
    });

    expect(parsed.mcp_servers[0]).toEqual({
      name: "RI-logs",
      description: "Download, unzip and grep log files",
      enabled: true,
      mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
      integration_alias: "ri-logs-alias",
      resolve_dynamic_values_in_arguments: false,
      tools: ["fetch_logs", "grep_logs"],
    });
  });

  it("preserves use_custom_config on an mcp_servers item", () => {
    const parsed = AssistantUpdateParamsSchema.parse({
      name: "a",
      description: "d",
      system_prompt: "x",
      project: "p",
      context: [],
      llm_model_type: "m",
      toolkits: [],
      conversation_starters: [],
      assistant_ids: [],
      mcp_servers: [
        {
          name: "RI-logs",
          enabled: true,
          use_custom_config: true,
        },
      ],
    });

    expect(parsed.mcp_servers[0]).toMatchObject({
      name: "RI-logs",
      enabled: true,
      use_custom_config: true,
    });
  });
});

describe("VirtualAssistantChatParamsSchema mcp_servers", () => {
  it("preserves saved-config MCP fields and undeclared keys on an mcp server", () => {
    const parsed = VirtualAssistantChatParamsSchema.parse({
      text: "hello",
      mcp_servers: [
        {
          name: "RI-logs",
          enabled: true,
          mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
          integration_alias: "ri-logs-alias",
          use_custom_config: true,
          resolve_dynamic_values_in_arguments: false,
          tools: ["fetch_logs"],
          future_backend_field: "x",
        },
      ],
    });

    expect(parsed.mcp_servers[0]).toMatchObject({
      name: "RI-logs",
      enabled: true,
      mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
      integration_alias: "ri-logs-alias",
      use_custom_config: true,
      resolve_dynamic_values_in_arguments: false,
      tools: ["fetch_logs"],
      future_backend_field: "x",
    });
  });

  it("forwards an undeclared key inside an mcp server config", () => {
    const parsed = VirtualAssistantChatParamsSchema.parse({
      text: "hello",
      mcp_servers: [
        {
          name: "remote",
          enabled: true,
          config: {
            url: "https://mcp.example.com",
            future_config_field: "y",
          },
        },
      ],
    });

    expect(parsed.mcp_servers[0].config).toMatchObject({
      url: "https://mcp.example.com",
      future_config_field: "y",
    });
  });

  it("accepts an explicit null config echoed back by the API", () => {
    const parsed = VirtualAssistantChatParamsSchema.parse({
      text: "hello",
      mcp_servers: [
        {
          name: "RI-logs",
          enabled: true,
          config: null,
          mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
        },
      ],
    });

    expect(parsed.mcp_servers[0]).toMatchObject({
      name: "RI-logs",
      enabled: true,
      config: null,
      mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
    });
  });
});

describe("AssistantCreateParamsSchema API-echo nulls", () => {
  const echoedFromApi = {
    name: "A",
    description: "D",
    icon_url: null,
    system_prompt: "P",
    project: "proj",
    context: [],
    llm_model_type: "gpt-4",
    toolkits: [],
    conversation_starters: [],
    assistant_ids: [],
    temperature: null,
    top_p: null,
    mcp_servers: [
      {
        name: "RI-logs",
        description: "Download, unzip and grep log files",
        enabled: true,
        mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
        config: null,
        mcp_connect_url: null,
        tools_tokens_size_limit: null,
        command: null,
        arguments: null,
      },
    ],
  };

  it("accepts an assistant fed straight back from the API, nulls and all", () => {
    const parsed = AssistantCreateParamsSchema.parse(echoedFromApi);

    expect(parsed.icon_url).toBeNull();
    expect(parsed.temperature).toBeNull();
    expect(parsed.top_p).toBeNull();
    expect(parsed.mcp_servers[0]).toMatchObject({
      mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
      mcp_connect_url: null,
      tools_tokens_size_limit: null,
      command: null,
      arguments: null,
    });
  });

  it("accepts the same payload through the update schema", () => {
    expect(() => AssistantUpdateParamsSchema.parse(echoedFromApi)).not.toThrow();
  });

  // A stdio server comes back with an inline config whose unused keys are null.
  it("accepts nulls inside an API-echoed mcp_servers config", () => {
    const parsed = AssistantCreateParamsSchema.parse({
      ...echoedFromApi,
      mcp_servers: [
        {
          name: "supabase-mcp",
          enabled: true,
          config: {
            command: "npx",
            url: null,
            args: ["-y", "@supabase/mcp-server-supabase@latest"],
            headers: {},
            env: {},
            type: null,
            auth_token: null,
            audience: null,
            tools: null,
          },
          command: null,
          arguments: null,
        },
      ],
    });

    expect(parsed.mcp_servers[0].config).toMatchObject({
      command: "npx",
      url: null,
      type: null,
      auth_token: null,
      audience: null,
      tools: null,
    });
  });

  // One guard for the whole class of bug: an assistant exactly as the API hands it back,
  // with a null in every place the backend model permits one, must survive assistants.update().
  it("accepts a full API response with a null in every nullable field", () => {
    const fromApi = {
      name: "A",
      description: "D",
      icon_url: null,
      system_prompt: "P",
      project: "proj",
      slug: null,
      llm_model_type: null,
      temperature: null,
      top_p: null,
      conversation_starters: [],
      assistant_ids: [],
      prompt_variables: null,
      categories: [{ id: "c1", name: "Quality assurance", description: null }],
      context: [{ context_type: "provider", name: "ctx" }],
      toolkits: [
        {
          toolkit: "tk",
          label: "TK",
          settings_config: false,
          is_external: false,
          settings: null,
          tools: [
            { name: "t", label: null, settings_config: false, user_description: null, settings: null },
          ],
        },
      ],
      mcp_servers: [
        {
          name: "RI-logs",
          description: null,
          enabled: true,
          mcp_config_id: "a6395977-3598-4a0a-bfb3-08463d484575",
          config: null,
          mcp_connect_url: null,
          tools_tokens_size_limit: null,
          command: null,
          arguments: null,
        },
      ],
    };

    expect(() => AssistantUpdateParamsSchema.parse(fromApi)).not.toThrow();
    expect(AssistantCreateParamsSchema.parse(fromApi).mcp_servers[0].description).toBeNull();
  });

  it("still rejects a config carrying both url and command after the null widening", () => {
    expect(() =>
      AssistantCreateParamsSchema.parse({
        ...echoedFromApi,
        mcp_servers: [{ name: "s", enabled: true, config: { command: "npx", url: "https://a" } }],
      }),
    ).toThrow();
  });
});

describe("AssistantCreateParamsSchema deselected_default_tools", () => {
  const base = {
    name: "A",
    description: "D",
    system_prompt: "P",
    project: "proj",
    context: [],
    llm_model_type: "gpt-4",
    toolkits: [],
    conversation_starters: [],
    assistant_ids: [],
    mcp_servers: [],
  };

  it("accepts a list of tool names", () => {
    const parsed = AssistantCreateParamsSchema.parse({
      ...base,
      deselected_default_tools: ["search_kb"],
    });
    expect(parsed.deselected_default_tools).toEqual(["search_kb"]);
  });

  it("accepts an empty list", () => {
    const parsed = AssistantUpdateParamsSchema.parse({ ...base, deselected_default_tools: [] });
    expect(parsed.deselected_default_tools).toEqual([]);
  });

  it("leaves the key absent when omitted", () => {
    const parsed = AssistantCreateParamsSchema.parse(base);
    expect("deselected_default_tools" in parsed).toBe(false);
  });

  it("rejects non-string items", () => {
    expect(() =>
      AssistantCreateParamsSchema.parse({ ...base, deselected_default_tools: [1] }),
    ).toThrow();
  });
});
