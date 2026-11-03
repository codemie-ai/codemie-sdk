# CodeMie Node.js SDK

TypeScript/JavaScript SDK for CodeMie services. This SDK provides a comprehensive interface to interact with CodeMie services, including LLM (Large Language Models), assistants, workflows, and tools.

## Table of Contents

- [CodeMie Node.js SDK](#codemie-nodejs-sdk)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Basic Usage](#basic-usage)
    - [ESM Import](#esm-import)
    - [CommonJS Import](#commonjs-import)
  - [Service Details](#service-details)
    - [LLM Service](#llm-service)
    - [Assistant Service](#assistant-service)
      - [Core Methods](#core-methods)
      - [Advanced Features](#advanced-features)
    - [Datasource Service](#datasource-service)
      - [Supported Datasource Types](#supported-datasource-types)
      - [Core Methods](#core-methods-1)
      - [Datasource Status](#datasource-status)
      - [Best Practices for Datasources](#best-practices-for-datasources)
    - [Integration Service](#integration-service)
      - [Integration Types](#integration-types)
      - [Core Methods](#core-methods-2)
      - [Best Practices for Integrations](#best-practices-for-integrations)
    - [Workflow Service](#workflow-service)
      - [Core Methods](#core-methods-3)
      - [Workflow Execution](#workflow-execution)
      - [Workflow Configuration](#workflow-configuration)
      - [Best Practices](#best-practices)
    - [Real World Examples](#real-world-examples)
      - [Setting Up an AI Assistant with Jira Integration](#setting-up-an-ai-assistant-with-jira-integration)
      - [Managing Workflows](#managing-workflows)
    - [Error Handling Best Practices](#error-handling-best-practices)
  - [Error Handling](#error-handling)
      - [Workflow Status Monitoring](#workflow-status-monitoring)
  - [Error Handling](#error-handling-1)
  - [TypeScript Support](#typescript-support)
  - [Development](#development)
    - [Pack and Publish](#pack-and-publish)
    - [Unit Tests](#unit-tests)
    - [E2E Tests](#e2e-tests)
  - [Support](#support)

## Installation

```bash
npm install codemie-sdk
```

or

```bash
yarn add codemie-sdk
```

## Usage

### Basic Usage

```typescript
import { CodeMieClient } from 'codemie-sdk';

// Initialize client with authentication parameters
const client = new CodeMieClient({
  auth_server_url: 'https://your-keycloak-host.example.com/auth',
  auth_realm_name: 'your-realm',
  codemie_api_domain: 'https://your-codemie-host.example.com/code-assistant-api',
  username: process.env.USERNAME,
  password: process.env.PASSWORD,
});

// Initialize the client (required before making any requests)
await client.initialize();
```

### Cookie-Based Authentication (SSO)

For SSO-based authentication using session cookies, you can skip the Keycloak configuration and provide cookies directly:

```typescript
import { CodeMieClient } from 'codemie-sdk';

// Initialize client with cookies (no Keycloak required)
const client = new CodeMieClient({
  codemie_api_domain: 'https://your-codemie-host.example.com/code-assistant-api',
  cookies: {
    'JSESSIONID': 'your-session-cookie',
    'XSRF-TOKEN': 'your-csrf-token'
  },
  verify_ssl: false
});

// No initialize() needed with cookie auth - ready to use immediately!
const assistants = await client.assistants.list();
```

**Key Differences with Cookie Auth:**
- ❌ No `initialize()` call needed - client is ready immediately
- ❌ No `auth_server_url` or `auth_realm_name` required
- ❌ `refreshToken()` will throw an error (not supported with cookies)
- ✅ `getToken()` returns `null` (no bearer token)
- ✅ Cookies are sent with every request via `Cookie` header
- ✅ Cookie management is handled by your SSO system

### ESM Import

```typescript
import { CodeMieClient } from 'codemie-sdk';

const client = new CodeMieClient({
  auth_server_url: process.env.AUTH_SERVER_URL || 'https://your-keycloak-host.example.com/auth',
  auth_realm_name: process.env.AUTH_REALM_NAME || 'your-realm',
  codemie_api_domain: process.env.CODEMIE_API_DOMAIN || 'https://your-codemie-host.example.com/code-assistant-api',
  username: process.env.USERNAME,
  password: process.env.PASSWORD,
});

// Initialize the client (required before making any requests)
await client.initialize();
```

### CommonJS Import

```javascript
const { CodeMieClient } = require('codemie-sdk');

const client = new CodeMieClient({
  // ... same configuration as above
});

// Initialize the client (required before making any requests)
await client.initialize();
```

## Service Details

### LLM Service

The LLM service provides access to language models and embedding models from various providers:

```typescript
import { LLMProvider, LLMModel } from 'codemie-sdk';

// List available LLM models
const llmModels = await client.llm.list();

// List available embedding models
const embeddingModels = await client.llm.listEmbeddings();
```

Example usage with provider and feature checks:

```typescript
// Get available models
const models = await client.llm.list();

// Find Azure OpenAI models
const azureModels = models.filter(m => m.provider === LLMProvider.AZURE_OPENAI);

// Find models supporting streaming and tools
const streamingToolModels = models.filter(m => 
  m.features.streaming && m.features.tools
);

// Get default model
const defaultModel = models.find(m => m.default);
```

### Assistant Service

The Assistant service allows you to manage and interact with CodeMie assistants:

#### Core Methods

1. **List Assistants**
```typescript
const assistants = await client.assistants.list({
  minimal_response: true,  // Return minimal assistant info
  scope: "visible_to_user",  // or "marketplace"
  page: 0,
  per_page: 12,
  filters: {key: "value"}  // Optional filters
});
```

2. **Get Assistant Details**
```typescript
// By ID
const assistant = await client.assistants.get("assistant-id");

// By Slug
const assistant = await client.assistants.getBySlug("assistant-slug");
```

3. **Create Assistant**
```typescript
const params: AssistantCreateParams = {
  name: "My Assistant",
  description: "Assistant description",
  system_prompt: "Assistant instructions",
  toolkits: [],
  project: "my_project",
  llm_model_type: "gpt-4o",
  context: [],
  conversation_starters: [],
  mcp_servers: [],
  assistant_ids: [],
  temperature: 0.7,
  top_p: 0.9,
  shared: false,
  is_react: false,
  is_global: false
};
await client.assistants.create(params);
```

4. **Update Assistant**
```typescript
const params: AssistantUpdateParams = {
  name: "Updated Name",
  description: "Updated description",
  system_prompt: "Updated instructions",
  project: "my_project",
  llm_model_type: "gpt-4",
  context: [],
  conversation_starters: [],
  mcp_servers: [],
  assistant_ids: [],
  toolkits: []
};
await client.assistants.update("assistant-id", params);
```

5. **Delete Assistant**
```typescript
await client.assistants.delete("assistant-id");
```

#### Advanced Features

6. **Chat with Assistant (with MCP header propagation)**
```typescript
const params: AssistantChatParams = {
  text: "Your message here",
  history: [],  // Previous conversation messages as ChatMessage[] or string
  // Optional parameters
  stream: false,  // Set to true for streaming response
  conversation_id: "optional-conversation-id",
  llm_model: "gpt-4o",
  system_prompt: "Override default system prompt",
  background_task: false,
  content_raw: "", // Raw content if needed
  top_k: 1,
  metadata: {}, // Additional metadata
  propagate_headers: true, // Enable propagation of X-* headers
  save_history: true, // Set to false to skip saving chat to history (defaults to true)
};

// Pass X-* headers to be forwarded to MCP servers
const response = await client.assistants.chat(
  "assistant-id",
  params,
  {
    "X-Tenant-ID": "tenant-abc-123",
    "X-User-ID": "user-456",
    "X-Request-ID": "req-123",
  }
);
```

6.a. **Chat with Assistant by slug (with MCP header propagation)**
```typescript
const params: AssistantChatParams = {
  text: "Your message here",
  propagate_headers: true,
};

const response = await client.assistants.chatBySlug(
  "assistant-slug",
  params,
  {
    "X-Environment": "production",
    "X-Feature-Flag-Beta": "true",
  }
);
```
7. **Utilize structured outputs with Assistant
Uzing zod objects
```typescript

const ResponseFormat = z.object({
  answer: z.string().describe("The answer to the user's question"),
  followup_question: z
    .string()
    .describe("A followup question the user could ask"),
});

const params: AssistantChatParams  = {
  text: "Your message here",
  history: [],  // Previous conversation messages as ChatMessage[] or string
  // Optional parameters
  stream: false,  // Set to true for streaming response
  conversation_id: "optional-conversation-id",
  llm_model: "gpt-4o",
  system_prompt: "Override default system prompt",
  background_task: false,
  content_raw: "", // Raw content if needed
  file_name: "", // For file processing
  top_k: 1,
  metadata: {}, // Additional metadata
  save_history: true, // Set to false to skip saving chat to history (defaults to true)
  output_schema: ResponseFormat
};

  const response = await client.assistants.chat(
    "b797be81-5ddb-4649-a445-96bbdde14809",
    params
  );
  // response.generated is object

```
Using JSON Schema in object format
```typescript
const schema = {
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/product.schema.json",
  "title": "ResponseFormatter",
  "type": "object",
  "properties": {
    "answer": {
      "description": "The answer to the user's question",
      "type": "string"
    },
    "followup_question": {
      "description": "A followup question the user could ask",
      "type": "string"
    }
  },
  "required": ["answer", "followup_question"]
}

const params: AssistantChatParams  = {
  text: "Your message here",
  history: [],  // Previous conversation messages as ChatMessage[] or string
  // Optional parameters
  stream: false,  // Set to true for streaming response
  conversation_id: "optional-conversation-id",
  llm_model: "gpt-4o",
  system_prompt: "Override default system prompt",
  background_task: false,
  content_raw: "", // Raw content if needed
  file_name: "", // For file processing
  top_k: 1,
  metadata: {}, // Additional metadata
  save_history: true, // Set to false to skip saving chat to history (defaults to true)
  output_schema: schema
};

  const response = await client.assistants.chat(
    "b797be81-5ddb-4649-a445-96bbdde14809",
    params
  );
  // response.generated is object
```

8. **Work with Prebuilt Assistants**
```typescript
// List prebuilt assistants
const prebuilt = await client.assistants.getPrebuilt();

// Get specific prebuilt assistant
const prebuiltAssistant = await client.assistants.getPrebuiltBySlug("assistant-slug");
```

9. **Get Available Tools**
```typescript
const tools = await client.assistants.getTools();
```

### Datasource Service

The Datasource service enables managing various types of data sources in CodeMie, including code repositories, Confluence spaces, Jira projects, files, and Google documents.

#### Supported Datasource Types

- `CODE`: Code repository datasources
- `CONFLUENCE`: Confluence knowledge base
- `JIRA`: Jira knowledge base
- `FILE`: File-based knowledge base
- `GOOGLE`: Google documents

#### Core Methods

1. **Create Datasource**
```typescript
import { DataSourceType, CodeDataSourceType } from 'codemie-sdk';

// Create Code Datasource
const codeParams: CodeDataSourceCreateParams = {
  type: DataSourceType.CODE,
  name: "my_repo",
  project_name: "my_project",
  description: "My code repository",
  shared_with_project: true,
  setting_id: null,
  link: "https://github.com/user/repo",
  branch: "main",
  index_type: CodeDataSourceType.CODE,
  files_filter: "*.ts",
  embeddings_model: "model_name",
  summarization_model: "gpt-4",
  docs_generation: false
};
 await client.datasources.create(codeParams);

// Create Confluence Datasource
const confluenceParams: ConfluenceDataSourceCreateParams = {
  type: DataSourceType.CONFLUENCE,
  name: "confluence_kb",
  project_name: "my_project",
  description: "Confluence space",
  shared_with_project: true,
  setting_id: null,
  cql: "space = 'MYSPACE'",
  include_restricted_content: false,
  include_archived_content: false,
  include_attachments: true,
  include_comments: true,
  keep_markdown_format: true,
  keep_newlines: true
};
await client.datasources.create(confluenceParams);

// Create Jira Datasource
const jiraParams: JiraDataSourceCreateParams = {
  type: DataSourceType.JIRA,
  name: "jira_kb",
  project_name: "my_project",
  description: "Jira project",
  shared_with_project: true,
  setting_id: null,
  jql: "project = 'MYPROJECT'"
};
await client.datasources.create(jiraParams);

// Create Google Doc Datasource
const googleParams: GoogleDataSourceCreateParams = {
  type: DataSourceType.GOOGLE,
  name: "google_doc",
  project_name: "my_project",
  description: "Google document",
  shared_with_project: true,
  setting_id: null,
  google_doc: "document_url"
};
await client.datasources.create(googleParams);
```

2. **Update Datasource**
```typescript
// Update Code Datasource
const updateParams: CodeDataSourceUpdateParams = {
  type: DataSourceType.CODE,
  name: "my_repo",
  project_name: "my_project",
  description: "Updated description",
  // Optional parameters
  shared_with_project: true,
  link: "https://github.com/user/repo",
  branch: "develop",
  index_type: CodeDataSourceType.CODE,
  full_reindex: true,
  skip_reindex: false,
  resume_indexing: false,
  incremental_reindex: false
};
const response = await client.datasources.update("datasource_id", updateParams);

// Update Confluence Datasource
const confluenceUpdateParams: ConfluenceDataSourceUpdateParams = {
  type: DataSourceType.CONFLUENCE,
  name: "confluence_kb",
  project_name: "my_project",
  description: "Updated description",
  cql: "space = 'UPDATED_SPACE'",
  full_reindex: true
};
const response = await client.datasources.update("datasource_id", confluenceUpdateParams);
```

3. **List Datasources**
```typescript
import { DataSourceType, DataSourceStatus, SortOrder } from 'codemie-sdk';

// List all datasources with filtering and pagination
const params: DataSourceListParams = {
  page: 0,
  per_page: 10,
  sort_key: "update_date",  // or "date"
  sort_order: SortOrder.DESC,  // or SortOrder.ASC
  datasource_types: [DataSourceType.CODE, DataSourceType.CONFLUENCE],
  projects: ["project1", "project2"],
  owner: "John Doe",
  status: DataSourceStatus.COMPLETED
};
const datasources = await client.datasources.list(params);

// Filter by multiple statuses
const inProgressAndFailed = await client.datasources.list({
  datasource_types: [DataSourceType.JIRA],
  status: [DataSourceStatus.IN_PROGRESS, DataSourceStatus.FAILED]
});
```

4. **Get Datasource Details**
```typescript
// Get single datasource by ID
const datasource = await client.datasources.get("datasource_id");
```

5. **Delete Datasource**
```typescript
// Delete datasource by ID
const result = await client.datasources.delete("datasource_id");
```

#### Datasource Status

```typescript
import { DataSourceStatus } from 'codemie-sdk';

// Available status constants
const statuses = {
  COMPLETED: DataSourceStatus.COMPLETED,    // Indexing completed successfully
  FAILED: DataSourceStatus.FAILED,          // Indexing failed
  FETCHING: DataSourceStatus.FETCHING,      // Fetching data from source
  IN_PROGRESS: DataSourceStatus.IN_PROGRESS // Processing/indexing in progress
};

// Example: Check datasource status
const datasource = await client.datasources.get("datasource_id");
if (datasource.status === DataSourceStatus.COMPLETED) {
  console.log("Datasource is ready to use");
} else if (datasource.status === DataSourceStatus.FAILED) {
  console.log("Datasource indexing failed:", datasource.error_message);
}
```

#### Datasource Limitations

- **This SDK cannot rename or move a datasource.** An update addresses a datasource by its project and
  name, so the SDK has no way to change either; the platform supports a project
  move, but the SDK does not expose it yet. A different name addresses a different datasource, or is not found.
  The search index and any assistant that uses the datasource refer to it by that name, so they would stop
  matching after a rename. To "rename", create a new datasource, point your assistants at it, then delete the
  old one.
- **File datasources are not supported by the Infrastructure-as-Code tooling** built on this SDK. Creating
  one needs the file contents uploaded together with the request (`files` in the create params), which a
  declarative document cannot carry. Use `client.datasources.create(...)` with the files directly instead.

#### Best Practices for Datasources

1. **Naming Convention**:
   - Use lowercase letters and underscores for datasource names
   - Keep names descriptive but concise

2. **Performance Optimization**:
   - Use appropriate filters when listing datasources
   - Consider pagination for large result sets
   - Choose appropriate reindex options based on your needs

3. **Error Handling**:
   - Always check datasource status after creation/update
   - Handle potential failures gracefully
   - Monitor processing information for issues

4. **Security**:
   - Be careful with sensitive data in filters and queries
   - Use proper access controls when sharing datasources
   - Regularly review and clean up unused datasources

### Integration Service

The Integration service manages both user and project-level integrations in CodeMie, allowing you to configure and manage various integration settings.

#### Integration Types

- `USER`: User-level integrations
- `PROJECT`: Project-level integrations

#### Core Methods

1. **List Integrations**
```typescript
import { IntegrationType } from 'codemie-sdk';

// List user integrations with pagination
const params: IntegrationListParams = {
  setting_type: IntegrationType.USER,
  page: 0,
  per_page: 10,
  filters: { status: "active" }  // optional filters
};
const userIntegrations = await client.integrations.list(params);

// List project integrations
const projectParams: IntegrationListParams = {
  setting_type: IntegrationType.PROJECT,
  per_page: 100
};
const projectIntegrations = await client.integrations.list(projectParams);
```

2. **Get Integration**
```typescript
// Get integration by ID
const integration = await client.integrations.get(
  "integration_id",
  IntegrationType.USER
);

// Get integration by alias
const integration = await client.integrations.getByAlias(
  "integration_alias",
  IntegrationType.PROJECT
);
```

3. **Create Integration**
```typescript
const params: IntegrationCreateParams = {
  setting_type: IntegrationType.USER,
  project_name: "my_project",
  credential_type: CredentialTypes.JIRA,
  credential_values: [
    { key: "url", value: "https://jira.example.com" },
    { key: "username", value: "user@example.com" },
    { key: "token", value: "api-token" }
  ],
  alias: "my_integration",
  default: false
};
await client.integrations.create(params);
```

4. **Update Integration**
```typescript
const params: IntegrationUpdateParams = {
  setting_type: IntegrationType.USER,
  project_name: "my_project",
  credential_type: CredentialTypes.JIRA,
  credential_values: [
    { key: "url", value: "https://jira.example.com" },
    { key: "username", value: "updated@example.com" },
    { key: "token", value: "new-api-token" }
  ],
  alias: "updated_integration"
};
await client.integrations.update("integration_id", params);
```

5. **Delete Integration**
```typescript
await client.integrations.delete(
  "integration_id",
  IntegrationType.USER
);
```

#### Best Practices for Integrations

1. **Error Handling**:
   - Handle `NotFoundError` when getting integrations by ID or alias
   - Validate integration settings before creation/update
   - Use appropriate setting type (USER/PROJECT) based on context

2. **Performance**:
   - Use pagination for listing integrations
   - Cache frequently accessed integrations when appropriate
   - Use filters to reduce result set size

3. **Security**:
   - Keep integration credentials secure
   - Regularly review and update integration settings
   - Use project-level integrations for team-wide settings
   - Use user-level integrations for personal settings

### Workflow Service

The Workflow service enables you to create, manage, and execute workflows in CodeMie. Workflows allow you to automate complex processes and integrate various CodeMie services.

#### Core Methods

1. **Create Workflow**
```typescript
// Create new workflow
const workflowParams = {
  name: "My Workflow",
  description: "Workflow description",
  project: "project-id",
  yamlConfig: "your-yaml-configuration",
  mode: "SEQUENTIAL",  // Optional, defaults to SEQUENTIAL
  shared: false,       // Optional, defaults to false
  iconUrl: "https://example.com/icon.png"  // Optional
};
const result = await client.workflows.createWorkflow(workflowParams);
```

2. **Update Workflow**
```typescript
// Update existing workflow
const updateParams = {
  name: "Updated Workflow",
  description: "Updated description",
  yamlConfig: "updated-yaml-config",
  mode: "PARALLEL",
  shared: false
};
const result = await client.workflows.update("workflow-id", updateParams);
```

3. **List Workflows**
```typescript
// List workflows with pagination and filtering
const workflows = await client.workflows.list({
  page: 0,
  perPage: 10,
  projects: ["project1", "project2"]  // Optional project filter
});
```

4. **Get Workflow Details**
```typescript
// Get workflow by ID
const workflow = await client.workflows.get("workflow-id");

// Get prebuilt workflows
const prebuiltWorkflows = await client.workflows.getPrebuilt();
```

5. **Delete Workflow**
```typescript
const result = await client.workflows.delete("workflow-id");
```

#### Workflow Execution

The SDK provides comprehensive workflow execution management through the WorkflowExecutionService:

1. **Run Workflow (with MCP header propagation)**
```typescript
// Enable propagation in payload and pass X-* headers to forward to MCP servers
const execution = await client.workflows.run(
  "workflow-id",
  "optional input",
  undefined, // fileName
  true,      // propagateHeaders
  {
    "X-Request-ID": "req-abc-123",
    "X-Source-App": "analytics-ui",
  },
);

// Get execution service for advanced operations
const executionService = client.workflows.executions("workflow-id");
```

2. **Manage Executions**
```typescript
// List workflow executions
const executions = await executionService.list({
  page: 0,
  perPage: 10
});

// Get execution details
const execution = await executionService.get("execution-id");

// Abort running execution
const result = await executionService.abort("execution-id");

// Resume interrupted execution with header propagation (query param + headers)
const result = await executionService.resume(
  "execution-id",
  true, // propagateHeaders
  {
    "X-Correlation-ID": "corr-456",
  }
);

// Delete all executions
const result = await executionService.deleteAll();
```

3. **Work with Execution States**
```typescript
// Get execution states
const states = await executionService.states("execution-id").list();

// Get state output
const stateOutput = await executionService.states("execution-id").getOutput("state-id");

// Example of monitoring workflow with state verification
async function verifyWorkflowExecution(executionService, executionId) {
  const execution = await executionService.get(executionId);
  
  if (execution.status === "SUCCEEDED") {
    // Get and verify states
    const states = await executionService.states(executionId).list();
    
    // States are ordered by completion date
    if (states.length >= 2) {
      console.log("Workflow completed successfully with multiple states");
    }
  } else if (execution.status === "FAILED") {
    console.log(`Workflow failed: ${execution.errorMessage}`);
  }
}
```

#### Workflow Configuration

Workflows support various configuration options:

1. **Modes**:
- `SEQUENTIAL`: Tasks execute in sequence
- `PARALLEL`: Tasks can execute simultaneously

2. **YAML Configuration**:
```yaml
name: Example Workflow
description: Workflow description
tasks:
  - name: task1
    type: llm
    config:
      prompt: "Your prompt here"
      model: "gpt-4o"
  
  - name: task2
    type: tool
    config:
      tool_name: "your-tool"
      parameters:
        param1: "value1"
```

#### Best Practices

1. **Workflow Design**:
- Keep workflows modular and focused
- Use clear, descriptive names for workflows and tasks
- Document workflow purpose and requirements
- Test workflows thoroughly before deployment

2. **Execution Management**:
- Monitor long-running workflows
- Implement proper error handling
- Use pagination for listing executions
- Clean up completed executions regularly

3. **Performance Optimization**:
- Choose appropriate workflow mode (SEQUENTIAL/PARALLEL)
- Manage resource usage in parallel workflows
- Consider task dependencies and ordering
- Use efficient task configurations

4. **Security**:
- Control workflow sharing carefully
- Validate user inputs
- Manage sensitive data appropriately
- Regular audit of workflow access

5. **Maintenance**:
- Regular review of workflow configurations
- Update workflows when dependencies change
- Monitor workflow performance
- Archive or remove unused workflows

### Real World Examples

This section provides practical examples of common use cases and complex workflows using the CodeMie SDK.

#### Setting Up an AI Assistant with Jira Integration

This example demonstrates setting up a complete workflow with Jira integration and AI assistant creation:

```typescript
import { 
    CodeMieClient, 
    AssistantCreateParams, 
    DataSourceCreateParams,
    CredentialTypes, 
    IntegrationType,
    DataSourceType,
    ContextType 
} from 'codemie-sdk';

async function setupAssistantWithJira() {
    const client = new CodeMieClient({/* auth config */});
    await client.initialize();

    // 1. Create Jira Integration
    const jiraIntegration = await client.integrations.create({
        project_name: "your_project",
        credential_type: CredentialTypes.JIRA,
        credential_values: [
            { key: "url", value: "https://your-jira.atlassian.net" },
            { key: "username", value: "your-email@example.com" },
            { key: "token", value: "your-api-token" }
        ],
        alias: "jira_integration",
        setting_type: IntegrationType.USER
    });

    // 2. Create Jira Datasource
    const datasource = await client.datasources.create({
        name: "jira_knowledge_base",
        project_name: "your_project",
        description: "Jira project knowledge base",
        setting_id: jiraIntegration.id,
        type: DataSourceType.JIRA,
        project_space_visible: true,
        jql: "project = 'YOUR-PROJECT'"
    });

    // 3. Create AI Assistant with Jira Context
    const assistant = await client.assistants.create({
        name: "Jira Helper Assistant",
        description: "Assistant for Jira queries",
        system_prompt: "You are a helpful assistant with access to Jira data",
        llm_model_type: "gpt-4",
        project: "your_project",
        context: [{
            name: datasource.name,
            context_type: ContextType.CODE
        }],
        toolkits: [
            {
                toolkit: "jira",
                tools: [
                    { name: "search_issues" },
                    { name: "create_issue" }
                ]
            }
        ]
    });

    return assistant;
}
```

#### Managing Workflows

Example of creating and executing a workflow:

```typescript
async function manageWorkflow() {
    const client = new CodeMieClient({/* auth config */});
    await client.initialize();

    // Create workflow
    const workflow = await client.workflows.create({
        name: "Document Processing",
        description: "Process and analyze documents",
        project: "your_project",
        mode: "SEQUENTIAL",
        yamlConfig: `
name: Document Processing
description: Process and analyze documents
tasks:
  - name: analyze_document
    type: llm
    config:
      prompt: "Analyze the following document:"
      model: "gpt-4"
  
  - name: create_summary
    type: tool
    config:
      tool_name: "document_summarizer"
      parameters:
        format: "markdown"
        max_length: 500
        `
    });

    // Execute workflow
    const execution = await client.workflows.run(workflow.id, {
        userInput: "Document content here"
    });

    // Monitor execution
    const executionService = client.workflows.executions(workflow.id);
    const states = await executionService.states(execution.id).list();
    
    // Get execution results
    const stateOutput = await executionService.states(execution.id)
        .getOutput(states[states.length - 1].id);
    
    return stateOutput;
}
```

### Error Handling Best Practices

Example of proper error handling in a complex operation:

```typescript
import { CodeMieError, ApiError, NotFoundError } from 'codemie-sdk';

async function robustOperation() {
    const client = new CodeMieClient({/* auth config */});
    
    try {
        await client.initialize();
        
        // Attempt to get or create assistant
        try {
            const assistant = await client.assistants.getBySlug("my-assistant");
            return assistant;
        } catch (error) {
            if (error instanceof NotFoundError) {
                // Assistant doesn't exist, create new one
                return await client.assistants.create({
                    name: "My Assistant",
                    slug: "my-assistant",
                    // ... other configuration
                });
            }
            throw error; // Re-throw if it's not a NotFoundError
        }
    } catch (error) {
        if (error instanceof ApiError) {
            console.error(`API Error: ${error.message}`, {
                statusCode: error.statusCode,
                details: error.details
            });
        } else if (error instanceof CodeMieError) {
            console.error(`SDK Error: ${error.message}`);
        } else {
            console.error(`Unexpected error: ${error}`);
        }
        throw error;
    }
}
```

## Error Handling

Implement proper error handling for workflow operations:

```typescript
try {
  const workflow = await client.workflows.get("workflow-id");
} catch (error) {
  if (error.statusCode === 404) {
    console.log("Workflow not found");
  } else {
    console.log(`API error: ${error.message}`);
  }
}
```

#### Workflow Status Monitoring

Monitor workflow execution status:

```typescript
async function monitorExecution(executionService, executionId) {
  while (true) {
    const execution = await executionService.get(executionId);
    const status = execution.status;
    
    if (status === "COMPLETED") {
      console.log("Workflow completed successfully");
      break;
    } else if (status === "FAILED") {
      console.log(`Workflow failed: ${execution.error}`);
      break;
    } else if (status === "ABORTED") {
      console.log("Workflow was aborted");
      break;
    }
      
    await new Promise(resolve => setTimeout(resolve, 5000)); // Poll every 5 seconds
  }
}
```

## Error Handling

The SDK throws typed errors that you can catch and handle:

```typescript
import { CodeMieError, ApiError, NotFoundError } from 'codemie-sdk';

try {
  await client.assistants.get('non-existent-id');
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('Assistant not found');
  } else if (error instanceof ApiError) {
    console.log('API error:', error.message, error.statusCode);
  } else if (error instanceof CodeMieError) {
    console.log('SDK error:', error.message);
  }
}
```

## TypeScript Support

The SDK is written in TypeScript and provides full type definitions. All interfaces and types are exported for use in your TypeScript projects.

```typescript
import type {
  Assistant,
  AssistantCreateParams,
  AssistantChatParams,
  ToolKitDetails
} from 'codemie-sdk';
```

## Development

### Pack and Publish

To build the SDK locally:

```bash
npm install
npm run build
```

To publish the SDK to npm, ensure you have the correct version in `package.json`, then run:

```bash
npm run build && npm publish --access=public
```

### Unit Tests

To run unit tests simply execute:

```bash
npm run test
```

### E2E Tests

To run end-to-end tests, ensure you have the necessary environment variables set up for authentication and API endpoints:

```bash
cp .env.e2e.example .env.e2e
```

Update the `.env.e2e` file with your credentials and API endpoints.

Then run the tests:

```bash
npm run test:e2e
```

### Assistant Versioning via SDK

The Node.js SDK exposes assistant versioning capabilities delivered in recent releases.

- List versions
```ts
const versions = await client.assistants.listVersions("assistant-id", { page: 0, per_page: 20 });
console.log(versions.map(v => v.version_number));
```

- Get specific version
```ts
const version = await client.assistants.getVersion("assistant-id", 2);
console.log(version.system_prompt);
```

- Compare two versions
```ts
const diff = await client.assistants.compareVersions("assistant-id", 1, 3);
console.log(diff.summary);
```

- Rollback to a version
```ts
const resp = await client.assistants.rollbackToVersion("assistant-id", 2);
console.log(resp);
```

- Chat with a specific version
```ts
import { z } from "zod";

const ResponseFormat = z.object({ answer: z.string(), followup_question: z.string() });
const params = { text: "Hi", stream: false, output_schema: ResponseFormat };

const resp = await client.assistants.chatWithVersion("assistant-id", 2, params);
console.log(resp.generated);
```

Quick CLI example
```bash
npx ts-node codemie-sdk/sdk/codemie-nodejs/examples/assistant_versions.ts <assistant_id> [version_number]
```

### Prompt Variables Support
The SDK supports assistant-level prompt variables that the backend already exposes.

Example:
```typescript
const params: AssistantCreateParams = {
  name: "My Assistant",
  description: "Assistant description",
  system_prompt: "Assistant instructions. Use {{project_name}} in responses.",
  toolkits: [],
  project: "my_project",
  llm_model_type: "gpt-4o",
  context: [],
  conversation_starters: [],
  mcp_servers: [],
  assistant_ids: [],
  prompt_variables: [
    { key: "project_name", default_value: "Delta", description: "Current project" },
    { key: "region", default_value: "eu" }
  ],
};
await client.assistants.create(params);

// Update
await client.assistants.update("assistant-id", {
  ...params,
  prompt_variables: [
    { key: "project_name", default_value: "Delta-Updated" },
    { key: "region", default_value: "us" },
  ],
});
```

Note: The backend validates duplicates; SDK passes them through and surfaces backend errors.

## Support

For questions and bug reports, open an issue via GitHub Issues. To report a security vulnerability, follow the policy in [SECURITY.md](../../SECURITY.md).
