/** Models for integration-related data structures */

/**
 * Credential types as constant object
 */
export const CredentialTypes = {
  JIRA: "Jira",
  CONFLUENCE: "Confluence",
  GIT: "Git",
  KUBERNETES: "Kubernetes",
  AWS: "AWS",
  GCP: "GCP",
  KEYCLOAK: "Keycloak",
  AZURE: "Azure",
  ELASTIC: "Elastic",
  OPENAPI: "OpenAPI",
  PLUGIN: "Plugin",
  FILESYSTEM: "FileSystem",
  SCHEDULER: "Scheduler",
  WEBHOOK: "Webhook",
  EMAIL: "Email",
  AZURE_DEVOPS: "AzureDevOps",
  SONAR: "Sonar",
  SQL: "SQL",
  TELEGRAM: "Telegram",
  ZEPHYR_SCALE: "ZephyrScale",
  SERVICE_NOW: "ServiceNow",
  DIAL: "DIAL",
  A2A: "A2A",
  MCP: "MCP",
  LITE_LLM: "LiteLLM",
  REPORT_PORTAL: "ReportPortal",
  XRAY: "Xray",
  SHAREPOINT: "SharePoint",
  GOOGLE_OAUTH: "GoogleOAuth",
  XWIKI: "XWiki",
  MS_TEAMS: "MSTeams",
  MS_EXCHANGE: "MSExchange",
} as const;

export type CredentialTypesType = (typeof CredentialTypes)[keyof typeof CredentialTypes];

/**
 * Integration types as constant object
 */
export const IntegrationType = {
  USER: "user",
  PROJECT: "project",
} as const;

export type IntegrationTypeType = (typeof IntegrationType)[keyof typeof IntegrationType];

/**
 * Model for credential values
 */
export interface CredentialValues {
  /** Key for the credential value */
  key: string;
  /** Value of the credential (can be any type) */
  value: unknown;
}

/**
 * Model for settings configuration
 */
export interface Integration {
  /** Integration ID */
  id: string;
  /** Creation date */
  date?: string;
  /** Last update date */
  update_date?: string;
  /** User ID */
  user_id?: string;
  /** Project name */
  project_name: string;
  /** Integration alias */
  alias?: string;
  /** Whether this is the default integration */
  default?: boolean;
  /** Whether this is a global integration */
  is_global?: boolean;
  /** Type of credential */
  credential_type: CredentialTypesType;
  /** List of credential values */
  credential_values: CredentialValues[];
  /** Type of integration */
  setting_type: IntegrationTypeType;
}

