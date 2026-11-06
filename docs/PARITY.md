# SDK Parity Guide

## The rule

The Python SDK (`sdk/codemie-python`) and the Node.js SDK (`sdk/codemie-nodejs`) expose the same CodeMie API. When you add or change a service or method in one SDK, make the matching change in the other in the same PR, or record the gap in the table below and say why in the PR description.

## Naming

- Node method and function names are the camelCase form of the Python snake_case name: `get_project_detail` is `getProjectDetail`.
- Payload and query keys stay snake_case in both SDKs (`is_project_admin`, `per_page`), because they are wire names.
- Argument order follows the Python signature. Note that `UserService` project methods take `(userId, projectName)`, while the same-named `ProjectService` methods take `(projectName, userId)`.

## Known behavioural differences

| Area | Python | Node.js |
|------|--------|---------|
| Response envelope | `wrap_response` unwraps the `data` field per call. | Each call unwraps `data` itself (falling back to the body when absent). A few endpoints return a raw body with no envelope (`listProjects`, `transferOwnership`) and are returned as is. |
| 404 | `requests.exceptions.HTTPError` with status 404. | `NotFoundError`. |
| Path segments | Not URL-encoded by the SDK. | Encoded with `encodeURIComponent`. |
| Bulk remove / assign limits | No client-side cap on `bulk_remove_users_from_project`. | `bulkRemoveUsersFromProject` accepts 1 to 100 ids and `bulkAssignUsersToProject` 1 to 1000 users; anything else throws a zod error before the request. This cap is the Node contract. Python should adopt the same cap, or the backend should enforce it, to close the divergence. |
| `project_exists` | Returns `False` only on a 404, re-raises other errors. | `projectExists` does the same with `NotFoundError`. |

## Services and methods

"Both" lists methods present on both sides under the naming rule (shown in Node form). "Python only" lists the Python names missing in Node. "Node only" lists Node methods with no same-named Python method (mostly renamed, for example `createProvider` versus `create_provider_datasource`). A row with `(gap)` has no Node module at all.

New in this change: `project_exists` / `projectExists` (both SDKs), the whole Node `ProjectService` (`client.projects`) and the 11 admin methods of the Node `UserService`.

| Python module | Node module | Both | Python only | Node only |
|---------------|-------------|------|-------------|-----------|
| `a2a` | - (gap) | - | `get_agent_card` | - |
| `activity_event` | - (gap) | - | `list_events`, `get_filter_options` | - |
| `admin` | - (gap) | - | `list_applications`, `create_application`, `create_local_user`, `list_users`, `delete_user` | - |
| `analytics` | `analytics` | `getSummaries`, `getCliSummary`, `getUsers`, `getAssistantsChats`, `getWorkflows`, `getToolsUsage`, `getWebhooksInvocation`, `getMcpServers`, `getMcpServersByUsers`, `getProjectsSpending`, `getLlmsUsage`, `getUsersSpending`, `getBudgetSoftLimit`, `getBudgetHardLimit`, `getUsersActivity`, `getProjectsActivity`, `getAgentsUsage`, `getCliAgents`, `getCliLlms`, `getCliUsers`, `getCliErrors`, `getCliRepositories` | `get_budget_usage`, `get_user_project_spending`, `get_leaderboard_summary`, `get_leaderboard_scores`, `get_leaderboard_tiers`, `get_leaderboard_top_performers`, `get_leaderboard_dimensions`, `get_leaderboard_entries`, `get_leaderboard_seasons`, `get_leaderboard_projects`, `get_leaderboard_framework`, `send_cli_hook_events`, `get_cli_sessions`, `ingest_cli_analytics_event_hooks`, `ingest_cli_analytics_logs`, `get_cli_analytics_cost`, `get_cli_analytics_users`, `get_cli_analytics_sessions`, `get_cli_analytics_session`, `get_cli_analytics_repositories` | - |
| `assistant` | `assistant` | `list`, `get`, `getBySlug`, `create`, `update`, `getTools`, `delete`, `getPrebuilt`, `getPrebuiltBySlug`, `listVersions`, `getVersion`, `chat`, `chatBySlug`, `askVirtual`, `compareVersions`, `rollbackToVersion`, `chatWithVersion`, `evaluate` | `get_context`, `get_builtin_subagents`, `upload_file_to_chat`, `export`, `publish`, `unpublish`, `marketplace_validate`, `resume_tool_call`, `react`, `remove_reactions`, `list_project_mapping`, `enable_for_project`, `disable_for_project`, `get_user_mapping`, `save_user_mapping`, `delete_user_mapping` | `listPaginated` |
| `categories` | `category` | `getCategories`, `listCategories`, `getCategory`, `createCategory`, `updateCategory`, `deleteCategory` | - | - |
| `codemie_guardrails` | - (gap) | - | `assign_guardrails` | - |
| `conversation` | `conversation` | `list`, `listByAssistantId`, `create`, `delete` | `get_conversation`, `chat`, `update`, `delete_all`, `get_files`, `list_folders`, `create_folder`, `update_folder`, `delete_folder`, `upsert_history`, `delete_history`, `delete_history_by_index`, `update_history_by_index`, `share_conversation`, `get_shared_conversation`, `create_feedback`, `delete_feedback`, `finish`, `finish_bulk`, `list_admin` | `get` |
| `cost_center` | - (gap) | - | `create_cost_center`, `delete_cost_center`, `list_cost_centers`, `get_budget_rollup` | - |
| `customer_config_service` | - (gap) | - | `list_declarations`, `get_config`, `is_mcp_custom_servers_disabled`, `save_setting`, `reset_setting` | - |
| `datasource` | `datasource` | `create`, `update`, `list`, `get`, `delete`, `getAssistantsUsingDatasource`, `getElasticsearchStats` | `create_file_datasource`, `create_provider_datasource`, `update_provider_datasource`, `health_check`, `get_jira_fields` | `createProvider` |
| `dynamic_config` | - (gap) | - | `set`, `delete` | - |
| `files` | `files` | `bulkUpload`, `getFile` | - | `upload` |
| `integration` | `integration` | `list`, `get`, `getByAlias`, `create`, `update`, `delete` | `list_available`, `test`, `transfer` | - |
| `llm` | `llm` | `list`, `listEmbeddings` | - | - |
| `mcp_configs` | - (gap) | - | `create`, `get`, `list`, `clone`, `update`, `delete` | - |
| `mermaid` | - (gap) | - | `generate_diagram` | - |
| `project` | `project` | `createProject`, `listProjects`, `getProjectDetail`, `updateProject`, `deleteProject`, `transferOwnership`, `assignUserToProject`, `updateUserProjectAssignment`, `removeUserFromProject`, `bulkAssignUsersToProject`, `bulkRemoveUsersFromProject`, `validateUsersFromCsv`, `importUsersFromCsv`, `projectExists` | - | - |
| `project_budget_groups` | - (gap) | - | `list_by_project`, `get`, `update`, `create`, `delete` | - |
| `servicenow_integration` | - (gap) | - | `list_projects`, `submit_budget_request` | - |
| `skill` | `skill` | `list`, `get`, `create`, `update`, `delete`, `importSkill`, `export`, `attachToAssistant`, `detachFromAssistant`, `getAssistantSkills`, `bulkAttachToAssistants`, `getSkillAssistants`, `listCompanionFiles`, `getCompanionFile`, `publish`, `unpublish`, `listCategories`, `getConfig`, `getUsers`, `react`, `removeReactions` | `record_event`, `get_events`, `get_events_stats`, `get_skill_stats`, `generate_instructions` | `listPaginated` |
| `task` | `task` | `get` | - | - |
| `usage_attribution` | - (gap) | - | `get_totals`, `get_status`, `get_cli_summary`, `get_settings`, `get_shared_projects`, `get_shared_project`, `get_repository_groups`, `get_repository_group`, `get_people`, `get_person`, `get_breakdown` | - |
| `user` | `user` | `aboutMe`, `getData`, `listAdminUsers`, `getAdminUser`, `updateAdminUser`, `getUserProjects`, `assignUserToProject`, `removeUserFromProject`, `updateUserProjectRole`, `setDefaultProject`, `clearDefaultProject`, `deactivateUser`, `reactivateUser` | - | - |
| `vendor_assistant` | - (gap) | - | `get_assistant_settings`, `get_assistants`, `get_assistant`, `get_assistant_version`, `get_assistant_aliases`, `install_assistants`, `uninstall_assistant` | - |
| `vendor_guardrail` | - (gap) | - | `get_guardrail_settings`, `get_guardrails`, `get_guardrail`, `get_guardrail_version`, `get_guardrail_versions`, `install_guardrails`, `uninstall_guardrail` | - |
| `vendor_knowledgebase` | - (gap) | - | `get_knowledgebase_settings`, `get_knowledgebases`, `get_knowledgebase`, `install_knowledgebases`, `uninstall_knowledgebase` | - |
| `vendor_runtime` | - (gap) | - | `get_runtime_settings`, `get_runtimes`, `get_runtime`, `get_endpoints`, `install_endpoints`, `uninstall_endpoint`, `get_endpoint` | - |
| `vendor_workflow` | - (gap) | - | `get_workflow_settings`, `get_workflows`, `get_workflow`, `get_workflow_aliases`, `install_workflows`, `uninstall_workflow` | - |
| `webhook` | - (gap) | - | `trigger`, `validate_msgraph_subscription` | - |
| `workflow` | `workflow` | `getPrebuilt`, `update`, `list`, `get`, `delete`, `run`, `evaluate`, `executions` | `create_workflow`, `generate`, `publish`, `marketplace_validate`, `unpublish` | `create` |
| `workflow_execution` | `workflow_execution` | `list`, `create`, `get`, `states`, `deleteAll`, `abort`, `resume` | `delete`, `get_transition_to`, `get_thoughts` | - |
| `workflow_execution_state` | `workflow_execution_state` | `list`, `getOutput` | - | - |
| `workspace` | - (gap) | - | `create`, `get_by_conversation`, `list_files`, `write_file`, `read_file`, `delete_file`, `execute_script` | - |

Python-only modules (no Node counterpart yet): `a2a`, `activity_event`, `admin`, `codemie_guardrails`, `cost_center`, `customer_config_service`, `dynamic_config`, `mcp_configs`, `mermaid`, `project_budget_groups`, `servicenow_integration`, `usage_attribution`, the `vendor_*` services, `webhook`, `workspace`. The table above regenerates from the two `services/` directories; update it when you change either.
