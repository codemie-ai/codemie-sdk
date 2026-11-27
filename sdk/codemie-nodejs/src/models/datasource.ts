/** Models for datasource service. */
import type { BaseUser, SortOrder, TokensUsage } from "./common";

/** Code datasource type options */
export const CodeDataSourceType = {
  CODE: "code",
  SUMMARY: "summary",
  CHUNK_SUMMARY: "chunk-summary",
} as const;
export type CodeDataSourceTypeType = (typeof CodeDataSourceType)[keyof typeof CodeDataSourceType];

/** Datasource type options */
export const DataSourceType = {
  CODE: "code",
  CONFLUENCE: "knowledge_base_confluence",
  JIRA: "knowledge_base_jira",
  FILE: "knowledge_base_file",
  GOOGLE: "llm_routing_google",
  GIT_FAQ: "knowledge_base_git_faq",
  PROVIDER: "provider",
  SUMMARY: "summary",
  CHUNK_SUMMARY: "chunk-summary",
  JSON: "knowledge_base_json",
  BEDROCK: "knowledge_base_bedrock",
  XRAY: "knowledge_base_xray",
  PLATFORM: "platform_marketplace_assistant",
  AZURE_DEVOPS_WIKI: "knowledge_base_azure_devops_wiki",
  AZURE_DEVOPS_WORK_ITEM: "knowledge_base_azure_devops_work_item",
  SHAREPOINT: "knowledge_base_sharepoint",
} as const;
export type DataSourceTypeType = (typeof DataSourceType)[keyof typeof DataSourceType];

/** Datasource status options */
export const DataSourceStatus = {
  COMPLETED: "completed",
  FAILED: "failed",
  FETCHING: "fetching",
  IN_PROGRESS: "in_progress",
} as const;
export type DataSourceStatusType = (typeof DataSourceStatus)[keyof typeof DataSourceStatus];

/** Base file model for file datasources */
export type File = Readonly<{
  /** File name */
  name: string;
  /** File content */
  content: string | Buffer<ArrayBuffer>;
  /** MIME type of the file */
  mime_type: string;
}>;

/** Confluence-specific configuration */
export interface Confluence {
  cql: string;
  include_restricted_content?: boolean;
  include_archived_content?: boolean;
  include_attachments?: boolean;
  include_comments?: boolean;
  keep_markdown_format?: boolean;
  keep_newlines?: boolean;
  max_pages?: number;
  pages_per_request?: number;
}

/** Jira-specific configuration */
export interface Jira {
  jql: string;
}

/**
 * Which issue content a Jira datasource indexes besides the issue itself.
 * Omitted on update keeps the stored value; omitted on create leaves both off.
 */
export interface JiraIncludeFlags {
  /** Index issue attachments as separate documents */
  include_attachments?: boolean;
  /** Index issue comments as separate documents */
  include_comments?: boolean;
}

/** Google-specific configuration */
export interface Google {
  googleDoc: string;
}

/** File-specific configuration */
export interface Files {
  files: File[];
}

/** Code repository configuration */
export interface Code {
  branch: string;
  docsGeneration?: boolean;
  embeddingsModel?: string;
  filesFilter?: string;
  indexType: CodeDataSourceTypeType;
  link: string;
  projectSpaceVisible?: boolean;
  prompt?: string;
  settingId: string;
  summarizationModel?: string;
}

/** Git FAQ (knowledge_base_git_faq) datasource fields */
export interface GitFaq {
  link: string;
  branch: string;
  files_filter?: string;
  embedding_model?: string;
}

/** Azure DevOps Wiki-specific configuration */
export interface AzureDevOpsWiki {
  wiki_query?: string;
  organization?: string;
  project?: string;
  wiki_name?: string;
}

/** Azure DevOps Work Item-specific configuration */
export interface AzureDevOpsWorkItem {
  wiql_query?: string;
  organization?: string;
  project?: string;
  /** Index work item attachments. Omitted on update keeps the stored value; on create uses the deployment default */
  include_attachments?: boolean;
  /** Index work item comments. Omitted on update keeps the stored value; on create uses the deployment default */
  include_comments?: boolean;
}

/** SharePoint authentication type */
export type SharePointAuthType = "integration" | "oauth_codemie" | "oauth_custom";

/** SharePoint-specific configuration (used in responses) */
export interface SharePoint {
  site_url: string;
  include_pages?: boolean;
  include_documents?: boolean;
  include_lists?: boolean;
  max_file_size_mb?: number;
  files_filter?: string;
  auth_type?: SharePointAuthType;
  oauth_client_id?: string;
  oauth_tenant_id?: string;
}

/** SharePoint-specific create/update parameters */
export interface BaseSharePointParams {
  /** SharePoint site URL (must start with https://) */
  site_url: string;
  /** Index SharePoint site pages */
  include_pages?: boolean;
  /** Index document libraries */
  include_documents?: boolean;
  /** Index list items */
  include_lists?: boolean;
  /** Maximum file size in MB to index (1–500, default 50) */
  max_file_size_mb?: number;
  /** Gitignore-style file/path filter */
  files_filter?: string;
  /** Authentication method */
  auth_type?: SharePointAuthType;
  /** OAuth access token (required for oauth_codemie and oauth_custom) */
  access_token?: string;
  /** Azure app client ID (oauth_custom only) */
  oauth_client_id?: string;
  /** Azure AD tenant ID (oauth_custom only) */
  oauth_tenant_id?: string;
  /** Override default embedding model */
  embedding_model?: string;
  /** Cron expression for scheduled reindexing */
  cron_expression?: string;
}

/** Elasticsearch statistics response */
export interface ElasticsearchStats {
  index_name: string;
  size_in_bytes: number;
}

/** Code Analysis provider datasource creation parameters */
export interface CodeAnalysisProviderCreateParams {
  name: string;
  description: string;
  project_name: string;
  shared_with_project?: boolean;
  branch: string;
  api_url: string;
  access_token: string;
  analyzer: string;
  datasource_root: string;
}

/** Code Exploration provider datasource creation parameters */
export interface CodeExplorationProviderCreateParams {
  name: string;
  description: string;
  project_name: string;
  shared_with_project?: boolean;
  code_analysis_datasource_ids: string[];
}

/** Provider datasource creation parameters */
export type ProviderDataSourceRequest =
  | CodeAnalysisProviderCreateParams
  | CodeExplorationProviderCreateParams;

/** Base data source DTO */
export interface BaseDataSourceCreateDto {
  name: string;
  project_name: string;
  description: string;
  project_space_visible: boolean;
  setting_id: string | null;
  type: DataSourceTypeType;
}

export interface ConfluenceDataSourceCreateDto extends BaseDataSourceCreateDto, Confluence {
  type: typeof DataSourceType.CONFLUENCE;
}
export interface JiraDataSourceCreateDto extends BaseDataSourceCreateDto, Jira, JiraIncludeFlags {
  type: typeof DataSourceType.JIRA;
}
export interface GoogleDataSourceCreateDto extends BaseDataSourceCreateDto, Google {
  type: typeof DataSourceType.GOOGLE;
}
export interface FileDataSourceCreateDto extends BaseDataSourceCreateDto, Files {
  type: typeof DataSourceType.FILE;
}
export interface CodeDataSourceCreateDto
  // override to comply with keys in json
  extends Omit<BaseDataSourceCreateDto, "setting_id" | "project_space_visible">,
    Code {
  type: typeof DataSourceType.CODE;
}
export interface AzureDevOpsWikiDataSourceCreateDto extends BaseDataSourceCreateDto, AzureDevOpsWiki {
  type: typeof DataSourceType.AZURE_DEVOPS_WIKI;
}
export interface AzureDevOpsWorkItemDataSourceCreateDto
  extends BaseDataSourceCreateDto,
    AzureDevOpsWorkItem {
  type: typeof DataSourceType.AZURE_DEVOPS_WORK_ITEM;
}
export interface XrayDataSourceCreateDto extends BaseDataSourceCreateDto, Jira {
  type: typeof DataSourceType.XRAY;
}
export interface SharePointDataSourceCreateDto extends BaseDataSourceCreateDto, BaseSharePointParams {
  type: typeof DataSourceType.SHAREPOINT;
}

export type DataSourceCreateDto =
  | ConfluenceDataSourceCreateDto
  | JiraDataSourceCreateDto
  | GoogleDataSourceCreateDto
  | FileDataSourceCreateDto
  | CodeDataSourceCreateDto
  | AzureDevOpsWikiDataSourceCreateDto
  | AzureDevOpsWorkItemDataSourceCreateDto
  | XrayDataSourceCreateDto
  | SharePointDataSourceCreateDto
  | BaseDataSourceCreateDto;

/** Base data source update DTO */
export interface BaseDataSourceUpdateDto {
  name: string;
  project_name: string;
  description?: string;
  project_space_visible?: boolean;
  setting_id?: string | null;
  type: DataSourceTypeType;
  full_reindex?: boolean;
  skip_reindex?: boolean;
  resume_indexing?: boolean;
  incremental_reindex?: boolean;
}

export interface ConfluenceDataSourceUpdateDto
  extends BaseDataSourceUpdateDto,
    Partial<Confluence> {
  type: typeof DataSourceType.CONFLUENCE;
}
export interface JiraDataSourceUpdateDto
  extends BaseDataSourceUpdateDto,
    Partial<Jira>,
    JiraIncludeFlags {
  type: typeof DataSourceType.JIRA;
}
export interface GoogleDataSourceUpdateDto extends BaseDataSourceUpdateDto, Partial<Google> {
  type: typeof DataSourceType.GOOGLE;
}
export interface FileDataSourceUpdateDto extends BaseDataSourceUpdateDto, Partial<Files> {
  type: typeof DataSourceType.FILE;
}
export interface CodeDataSourceUpdateDto
  extends Omit<BaseDataSourceUpdateDto, "setting_id" | "project_space_visible">,
    Partial<Code> {
  type: typeof DataSourceType.CODE;
}
export interface AzureDevOpsWikiDataSourceUpdateDto
  extends BaseDataSourceUpdateDto,
    Partial<AzureDevOpsWiki> {
  type: typeof DataSourceType.AZURE_DEVOPS_WIKI;
}
export interface AzureDevOpsWorkItemDataSourceUpdateDto
  extends BaseDataSourceUpdateDto,
    Partial<AzureDevOpsWorkItem> {
  type: typeof DataSourceType.AZURE_DEVOPS_WORK_ITEM;
}
export interface XrayDataSourceUpdateDto extends BaseDataSourceUpdateDto, Partial<Jira> {
  type: typeof DataSourceType.XRAY;
}
export interface SharePointDataSourceUpdateDto
  extends BaseDataSourceUpdateDto,
    Partial<BaseSharePointParams> {
  type: typeof DataSourceType.SHAREPOINT;
}

export type DataSourceUpdateDto =
  | ConfluenceDataSourceUpdateDto
  | JiraDataSourceUpdateDto
  | GoogleDataSourceUpdateDto
  | FileDataSourceUpdateDto
  | CodeDataSourceUpdateDto
  | AzureDevOpsWikiDataSourceUpdateDto
  | AzureDevOpsWorkItemDataSourceUpdateDto
  | XrayDataSourceUpdateDto
  | SharePointDataSourceUpdateDto
  | BaseDataSourceUpdateDto;

/** Processing information for datasource */
export interface DataSourceProcessingInfoResponse {
  /** Total number of documents processed */
  total_documents?: number;
  /** Number of documents skipped */
  skipped_documents?: number;
  /** Total size in kilobytes */
  total_size_kb?: number;
  /** Average file size in bytes */
  average_file_size_bytes?: number;
  /** List of unique file extensions */
  unique_extensions?: string[];
  /** Filtered documents count or list */
  filtered_documents?: number | string[];
  /** Number of processed documents */
  documents_count_key?: number;
}

/** Processing information for datasource */
export interface DataSourceProcessingInfo {
  /** Total number of documents processed */
  total_documents_count?: number;
  /** Number of documents skipped */
  skipped_documents_count?: number;
  /** Total size in kilobytes */
  total_size_kb?: number;
  /** Average file size in bytes */
  average_file_size_bytes?: number;
  /** List of unique file extensions */
  unique_extensions?: string[];
  /** Filtered documents count or list */
  filtered_documents?: number | string[];
  /** Number of processed documents */
  processed_documents_count?: number;
}

export type DataSourceResponse = BaseDataSourceResponse | CodeDataSourceResponse | GitFaqDataSourceResponse;

/** Datasource response interface */
export interface BaseDataSourceResponse {
  /** Unique identifier */
  id: string;
  /** Project name */
  project_name: string;
  /** Datasource name */
  repo_name: string;
  /** Description */
  description?: string;
  /** Type of datasource */
  index_type: DataSourceTypeType;
  /** Embeddings model used */
  embeddings_model?: string;
  /** Whether datasource has an error */
  error?: boolean;
  /** Whether datasource indexing is complete */
  completed?: boolean;
  /** Whether datasource is currently fetching */
  is_fetching?: boolean;
  /** Whether datasource is queued */
  is_queued?: boolean;
  /** Setting ID reference */
  setting_id?: string;
  /** Creation date */
  date: string;
  /** Creator information */
  created_by: BaseUser;
  /** Whether shared with project */
  project_space_visible: boolean;
  /** Last update date */
  update_date: string;
  /** Error message if failed */
  text?: string;
  /** User abilities list */
  user_abilities: string[];
  /** Processing information */
  processing_info?: DataSourceProcessingInfoResponse;
  /** List of processed documents */
  processed_files?: string[];
  /** Token usage statistics */
  tokens_usage?: TokensUsage;
  /** Jira-specific configuration */
  jira?: Jira & JiraIncludeFlags;
  /** Confluence-specific configuration */
  confluence?: Confluence;
  /** Google document link */
  google_doc_link?: string;
  /** Azure DevOps Wiki-specific configuration */
  azure_devops_wiki?: AzureDevOpsWiki;
  /** Azure DevOps Work Item-specific configuration */
  azure_devops_work_item?: AzureDevOpsWorkItem;
  /** SharePoint-specific configuration */
  sharepoint?: SharePoint;
}

export type CodeDataSourceResponse = BaseDataSourceResponse & {
  /** Repository URL */
  link: string;
  /** Branch name */
  branch: string;
  /** Type of index to create */
  index_type: CodeDataSourceTypeType;
  /** Files filter pattern */
  files_filter?: string;
  /** Embeddings model to use */
  embeddings_model?: string;
  /** Summarization model to use */
  summarization_model?: string;
  /** Custom summarization prompt */
  prompt?: string;
  /** Enable documentation generation */
  docs_generation?: boolean;
}

/** Git FAQ datasource response */
export type GitFaqDataSourceResponse = BaseDataSourceResponse & {
  link?: string | null;
  branch?: string | null;
  files_filter?: string | null;
};

/** Datasource model */
export interface DataSource {
  /** Unique identifier */
  id: string;
  /** Project name */
  project_name: string;
  /** Datasource name */
  name: string;
  /** Description */
  description?: string;
  /** Type of datasource */
  type: DataSourceTypeType;
  /** Embeddings model used */
  embeddings_model?: string;
  /** Current status */
  status: DataSourceStatusType;
  /** Setting ID reference */
  setting_id?: string | null;
  /** Creation date */
  created_date: string;
  /** Creator information */
  created_by: BaseUser;
  /** Whether shared with project */
  shared_with_project: boolean;
  /** Last update date */
  update_date: string;
  /** Error message if failed */
  error_message?: string;
  /** User abilities list */
  user_abilities: string[];
  /** Processing information */
  processing_info?: DataSourceProcessingInfo;
  /** List of processed documents */
  processed_documents?: string[];
  /** Token usage statistics */
  tokens_usage?: TokensUsage;
  /** Code-specific configuration */
  code?: Partial<Code>;
  git_faq?: Partial<GitFaq>;
  /** Jira-specific configuration */
  jira?: Jira & JiraIncludeFlags;
  /** Confluence-specific configuration */
  confluence?: Confluence;
  /** Google document link */
  google_doc_link?: string;
  /** Azure DevOps Wiki-specific configuration */
  azure_devops_wiki?: AzureDevOpsWiki;
  /** Azure DevOps Work Item-specific configuration */
  azure_devops_work_item?: AzureDevOpsWorkItem;
  /** SharePoint-specific configuration */
  sharepoint?: SharePoint;
}

/** DataSource fetch parameters */
export type DataSourceListParams = {
  page?: number;
  per_page?: number;
  sort_key?: "date" | "update_date";
  sort_order?: SortOrder;
  datasource_types?: DataSourceTypeType[];
  projects?: string[];
  owner?: string;
  status?: DataSourceStatusType;
  search?: string;
};

// Datasources create and update parameters
export interface BaseConfluenceParams {
  /** Confluence Query Language string */
  cql: string;
  /** Include restricted content */
  include_restricted_content?: boolean;
  /** Include archived content */
  include_archived_content?: boolean;
  /** Include attachments */
  include_attachments?: boolean;
  /** Include comments */
  include_comments?: boolean;
  /** Keep markdown format */
  keep_markdown_format?: boolean;
  /** Keep newlines */
  keep_newlines?: boolean;
  /** Maximum pages to fetch */
  max_pages?: number;
  /** Pages per request */
  pages_per_request?: number;
}

export interface BaseJiraParams {
  /** Jira Query Language string */
  jql: string;
}

/** File-specific configuration */
export interface BaseFileParams {
  /** List of files with their content and mime type */
  files: File[];
}

/** Google-specific configuration */
export interface BaseGoogleParams {
  /** Google document ID or URL */
  google_doc: string;
}

/** Code repository configuration */
/** Git FAQ (knowledge_base_git_faq) datasource configuration */
export interface BaseGitFaqParams {
  /** Repository URL */
  link: string;
  /** Branch name */
  branch: string;
  /** Gitignore-style include/exclude patterns; empty indexes every .md file in the repo */
  files_filter?: string;
  /** Embedding model used for chunk vectors */
  embedding_model?: string;
}

export interface BaseCodeParams {
  /** Repository URL */
  link: string;
  /** Branch name */
  branch: string;
  /** Type of index to create */
  index_type: CodeDataSourceTypeType;
  /** Files filter pattern */
  files_filter?: string;
  /** Embeddings model to use */
  embeddings_model?: string;
  /** Summarization model to use */
  summarization_model?: string;
  /** Custom summarization prompt */
  prompt?: string;
  /** Enable documentation generation */
  docs_generation?: boolean;
}

export interface BaseDataSourceCreateParams {
  /** Name of the datasource */
  name: string;
  /** Project name */
  project_name: string;
  /** Description of the datasource */
  description: string;
  /** Whether to share with project */
  shared_with_project: boolean;
  /** Setting ID reference */
  setting_id: string | null;
  /** Type of datasource */
  type: DataSourceTypeType;
}

export interface ConfluenceDataSourceCreateParams
  extends BaseDataSourceCreateParams,
    BaseConfluenceParams {
  type: typeof DataSourceType.CONFLUENCE;
}
export interface JiraDataSourceCreateParams
  extends BaseDataSourceCreateParams,
    BaseJiraParams,
    JiraIncludeFlags {
  type: typeof DataSourceType.JIRA;
}
export interface GoogleDataSourceCreateParams extends BaseDataSourceCreateParams, BaseGoogleParams {
  type: typeof DataSourceType.GOOGLE;
}
export interface GitFaqDataSourceCreateParams extends BaseDataSourceCreateParams, BaseGitFaqParams {
  type: typeof DataSourceType.GIT_FAQ;
}
export interface FileDataSourceCreateParams extends BaseDataSourceCreateParams, BaseFileParams {
  type: typeof DataSourceType.FILE;
}
export interface CodeDataSourceCreateParams extends BaseDataSourceCreateParams, BaseCodeParams {
  type: typeof DataSourceType.CODE;
}
export interface AzureDevOpsWikiDataSourceCreateParams
  extends BaseDataSourceCreateParams,
    AzureDevOpsWiki {
  type: typeof DataSourceType.AZURE_DEVOPS_WIKI;
}
export interface AzureDevOpsWorkItemDataSourceCreateParams
  extends BaseDataSourceCreateParams,
    AzureDevOpsWorkItem {
  type: typeof DataSourceType.AZURE_DEVOPS_WORK_ITEM;
}
export interface XrayDataSourceCreateParams extends BaseDataSourceCreateParams, BaseJiraParams {
  type: typeof DataSourceType.XRAY;
}
export interface SharePointDataSourceCreateParams
  extends BaseDataSourceCreateParams,
    BaseSharePointParams {
  type: typeof DataSourceType.SHAREPOINT;
}
export interface OtherDataSourceCreateParams extends BaseDataSourceCreateParams {
  type:
    | typeof DataSourceType.PROVIDER
    | typeof DataSourceType.SUMMARY
    | typeof DataSourceType.CHUNK_SUMMARY
    | typeof DataSourceType.JSON
    | typeof DataSourceType.PLATFORM;
}

/** DataSource create parameters */
export type DataSourceCreateParams =
  | ConfluenceDataSourceCreateParams
  | JiraDataSourceCreateParams
  | GoogleDataSourceCreateParams
  | GitFaqDataSourceCreateParams
  | FileDataSourceCreateParams
  | CodeDataSourceCreateParams
  | AzureDevOpsWikiDataSourceCreateParams
  | AzureDevOpsWorkItemDataSourceCreateParams
  | XrayDataSourceCreateParams
  | SharePointDataSourceCreateParams
  | OtherDataSourceCreateParams;

export interface BaseDataSourceUpdateParams {
  /** Type of datasource */
  type: DataSourceTypeType;
  /** Name of the datasource */
  name: string;
  /** Project name */
  project_name: string;
  /** Description of the datasource */
  description?: string;
  /** Whether to share with project */
  shared_with_project?: boolean;
  /** Setting ID reference */
  setting_id?: string | null;
  /** Perform full reindex */
  full_reindex?: boolean;
  /** Skip reindex operation */
  skip_reindex?: boolean;
  /** Resume interrupted indexing */
  resume_indexing?: boolean;
  /** Perform incremental reindex */
  incremental_reindex?: boolean;
}

export interface ConfluenceDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseConfluenceParams> {
  type: typeof DataSourceType.CONFLUENCE;
}
export interface JiraDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseJiraParams>,
    JiraIncludeFlags {
  type: typeof DataSourceType.JIRA;
}
export interface GoogleDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseGoogleParams> {
  type: typeof DataSourceType.GOOGLE;
}
export interface GitFaqDataSourceUpdateParams extends BaseDataSourceUpdateParams, Partial<BaseGitFaqParams> {
  type: typeof DataSourceType.GIT_FAQ;
}
export interface FileDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseFileParams> {
  type: typeof DataSourceType.FILE;
}
export interface CodeDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseCodeParams> {
  type: typeof DataSourceType.CODE;
}
export interface AzureDevOpsWikiDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<AzureDevOpsWiki> {
  type: typeof DataSourceType.AZURE_DEVOPS_WIKI;
}
export interface AzureDevOpsWorkItemDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<AzureDevOpsWorkItem> {
  type: typeof DataSourceType.AZURE_DEVOPS_WORK_ITEM;
}
export interface XrayDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseJiraParams> {
  type: typeof DataSourceType.XRAY;
}
export interface SharePointDataSourceUpdateParams
  extends BaseDataSourceUpdateParams,
    Partial<BaseSharePointParams> {
  type: typeof DataSourceType.SHAREPOINT;
}
export interface OtherDataSourceUpdateParams extends BaseDataSourceUpdateParams {
  type:
    | typeof DataSourceType.PROVIDER
    | typeof DataSourceType.SUMMARY
    | typeof DataSourceType.CHUNK_SUMMARY
    | typeof DataSourceType.JSON
    | typeof DataSourceType.PLATFORM;
}

/** DataSource update parameters */
export type DataSourceUpdateParams =
  | ConfluenceDataSourceUpdateParams
  | JiraDataSourceUpdateParams
  | GoogleDataSourceUpdateParams
  | GitFaqDataSourceUpdateParams
  | FileDataSourceUpdateParams
  | CodeDataSourceUpdateParams
  | AzureDevOpsWikiDataSourceUpdateParams
  | AzureDevOpsWorkItemDataSourceUpdateParams
  | XrayDataSourceUpdateParams
  | SharePointDataSourceUpdateParams
  | OtherDataSourceUpdateParams;
