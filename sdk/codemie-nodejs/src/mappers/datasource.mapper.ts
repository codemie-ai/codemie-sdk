import type {
  AzureDevOpsWikiDataSourceCreateParams,
  AzureDevOpsWikiDataSourceUpdateParams,
  AzureDevOpsWorkItemDataSourceCreateParams,
  AzureDevOpsWorkItemDataSourceUpdateParams,
  Code,
  GitFaq,
  CodeDataSourceResponse,
  GitFaqDataSourceResponse,
  CodeDataSourceCreateParams,
  CodeDataSourceUpdateParams,
  ConfluenceDataSourceCreateParams,
  ConfluenceDataSourceUpdateParams,
  DataSource,
  DataSourceCreateDto,
  DataSourceCreateParams,
  DataSourceProcessingInfo,
  DataSourceProcessingInfoResponse,
  DataSourceResponse,
  DataSourceUpdateDto,
  DataSourceUpdateParams,
  FileDataSourceCreateParams,
  FileDataSourceUpdateParams,
  GoogleDataSourceCreateParams,
  GitFaqDataSourceCreateParams,
  GitFaqDataSourceUpdateParams,
  GoogleDataSourceUpdateParams,
  JiraDataSourceCreateParams,
  JiraDataSourceUpdateParams,
  SharePointDataSourceCreateParams,
  SharePointDataSourceUpdateParams,
  XrayDataSourceCreateParams,
  XrayDataSourceUpdateParams,
  DataSourceStatusType,
} from "../models";
import { DataSourceStatus, DataSourceType } from "../models/datasource";
import { omitUndefined } from "../utils/helpers";

export class DatasourceMapper {
  /** Transforms API response into a client-friendly DataSource model, maintaining API-agnostic interface */
  static mapDatasourceResponse(response: DataSourceResponse): DataSource {
    return omitUndefined({
      ...DatasourceMapper.mapDataSourceResponseCommonFields(response),
      ...(response.index_type === DataSourceType.JIRA && {
        jira: response.jira,
      }),
      ...(response.index_type === DataSourceType.CONFLUENCE && {
        confluence: response.confluence,
      }),
      ...(response.index_type === DataSourceType.GOOGLE && {
        google_doc: response.google_doc_link,
      }),
      ...(response.index_type === DataSourceType.GIT_FAQ && {
        git_faq: DatasourceMapper.extractGitFaqDataSourceResponseFields(response as GitFaqDataSourceResponse),
      }),
      ...(response.index_type === DataSourceType.CODE && {
        code: DatasourceMapper.extractCodeDataSourceResponseFields(
          response as CodeDataSourceResponse,
        ),
      }),
      ...(response.index_type === DataSourceType.AZURE_DEVOPS_WIKI && {
        azure_devops_wiki: response.azure_devops_wiki,
      }),
      ...(response.index_type === DataSourceType.AZURE_DEVOPS_WORK_ITEM && {
        azure_devops_work_item: response.azure_devops_work_item,
      }),
      ...(response.index_type === DataSourceType.SHAREPOINT && {
        sharepoint: response.sharepoint,
      }),
    });
  }

  static mapDataSourceResponseCommonFields(response: DataSourceResponse) {
    let status: DataSourceStatusType;
    if (response.error) {
      status = DataSourceStatus.FAILED;
    } else if (response.completed) {
      status = DataSourceStatus.COMPLETED;
    } else if (response.is_fetching) {
      status = DataSourceStatus.FETCHING;
    } else {
      status = DataSourceStatus.IN_PROGRESS;
    }

    return {
      id: response.id,
      created_by: response.created_by,
      created_date: response.date,
      description: response.description,
      embeddings_model: response.embeddings_model,
      error_message: response.text,
      name: response.repo_name,
      processed_documents: response.processed_files,
      processing_info: response.processing_info
        ? DatasourceMapper.mapDatasourceProcessingInfoResponse(response.processing_info)
        : undefined,
      project_name: response.project_name,
      setting_id: response.setting_id,
      shared_with_project: response.project_space_visible,
      status,
      tokens_usage: response.tokens_usage,
      type: response.index_type,
      update_date: response.update_date,
      user_abilities: response.user_abilities,
    };
  }

  static extractCodeDataSourceResponseFields(response: CodeDataSourceResponse): Partial<Code> {
    return omitUndefined({
      branch: response.branch,
      docsGeneration: response.docs_generation || false,
      embeddingsModel: response.embeddings_model,
      filesFilter: response.files_filter,
      indexType: response.index_type,
      link: response.link,
      projectSpaceVisible: response.project_space_visible || false,
      prompt: response.prompt,
      settingId: response.setting_id,
      summarizationModel: response.summarization_model,
    });
  }

  static extractGitFaqDataSourceResponseFields(response: GitFaqDataSourceResponse): Partial<GitFaq> {
    return omitUndefined({
      link: response.link ?? undefined,
      branch: response.branch ?? undefined,
      files_filter: response.files_filter ?? undefined,
    });
  }

  /** Converts processing metadata from API format to client model format with consistent property naming */
  static mapDatasourceProcessingInfoResponse(
    response: DataSourceProcessingInfoResponse,
  ): DataSourceProcessingInfo {
    return omitUndefined({
      total_documents_count: response.total_documents,
      skipped_documents_count: response.skipped_documents,
      total_size_kb: response.total_size_kb,
      average_file_size_bytes: response.average_file_size_bytes,
      unique_extensions: response.unique_extensions,
      filtered_documents: response.filtered_documents,
      processed_documents_count: response.documents_count_key,
    });
  }

  /** Transforms datasource creation parameters into DTO format, applying type-specific mappings based on datasource type */
  static mapDatasourceCreateToDto(create: DataSourceCreateParams): DataSourceCreateDto {
    return omitUndefined({
      ...DatasourceMapper.mapCommonDataSourceParams(create),
      ...(create.type === DataSourceType.CONFLUENCE &&
        DatasourceMapper.mapConfluenceDataSourceParams(create as ConfluenceDataSourceCreateParams)),
      ...(create.type === DataSourceType.JIRA &&
        DatasourceMapper.mapJiraDataSourceParams(create as JiraDataSourceCreateParams)),
      ...(create.type === DataSourceType.GOOGLE &&
        DatasourceMapper.mapGoogleDataSourceParams(create as GoogleDataSourceCreateParams)),
      ...(create.type === DataSourceType.GIT_FAQ &&
        DatasourceMapper.mapGitFaqDataSourceParams(create as GitFaqDataSourceCreateParams)),
      ...(create.type === DataSourceType.FILE &&
        DatasourceMapper.mapFileDataSourceParams(create as FileDataSourceCreateParams)),
      ...(create.type === DataSourceType.CODE &&
        DatasourceMapper.mapCodeDataSourceParams(create as CodeDataSourceCreateParams)),
      ...(create.type === DataSourceType.AZURE_DEVOPS_WIKI &&
        DatasourceMapper.mapAzureDevOpsWikiParams(
          create as AzureDevOpsWikiDataSourceCreateParams,
        )),
      ...(create.type === DataSourceType.AZURE_DEVOPS_WORK_ITEM &&
        DatasourceMapper.mapAzureDevOpsWorkItemParams(
          create as AzureDevOpsWorkItemDataSourceCreateParams,
        )),
      ...(create.type === DataSourceType.XRAY &&
        DatasourceMapper.mapXrayDataSourceParams(create as XrayDataSourceCreateParams)),
      ...(create.type === DataSourceType.SHAREPOINT &&
        DatasourceMapper.mapSharePointParams(create as SharePointDataSourceCreateParams)),
    });
  }

  /** Converts datasource update parameters to DTO format with conditional inclusion of type-specific properties */
  static mapDatasourceUpdateToDto(update: DataSourceUpdateParams): DataSourceUpdateDto {
    return omitUndefined({
      ...DatasourceMapper.mapCommonUpdateDataSourceParams(update),
      ...(update.type === DataSourceType.CONFLUENCE &&
        DatasourceMapper.mapConfluenceDataSourceParams(update as ConfluenceDataSourceUpdateParams)),
      ...(update.type === DataSourceType.JIRA &&
        DatasourceMapper.mapJiraDataSourceParams(update as JiraDataSourceUpdateParams)),
      ...(update.type === DataSourceType.GOOGLE &&
        DatasourceMapper.mapGoogleDataSourceParams(update as GoogleDataSourceUpdateParams)),
      ...(update.type === DataSourceType.GIT_FAQ &&
        DatasourceMapper.mapGitFaqDataSourceParams(update as GitFaqDataSourceUpdateParams)),
      ...(update.type === DataSourceType.FILE &&
        DatasourceMapper.mapFileDataSourceParams(update as FileDataSourceUpdateParams)),
      ...(update.type === DataSourceType.CODE &&
        DatasourceMapper.mapCodeDataSourceParams(update as CodeDataSourceUpdateParams)),
      ...(update.type === DataSourceType.AZURE_DEVOPS_WIKI &&
        DatasourceMapper.mapAzureDevOpsWikiParams(
          update as AzureDevOpsWikiDataSourceUpdateParams,
        )),
      ...(update.type === DataSourceType.AZURE_DEVOPS_WORK_ITEM &&
        DatasourceMapper.mapAzureDevOpsWorkItemParams(
          update as AzureDevOpsWorkItemDataSourceUpdateParams,
        )),
      ...(update.type === DataSourceType.XRAY &&
        DatasourceMapper.mapXrayDataSourceParams(update as XrayDataSourceUpdateParams)),
      ...(update.type === DataSourceType.SHAREPOINT &&
        DatasourceMapper.mapSharePointParams(update as SharePointDataSourceUpdateParams)),
    });
  }

  /** Maps Confluence-specific configuration parameters for content filtering and pagination options */
  private static mapConfluenceDataSourceParams<
    T extends ConfluenceDataSourceCreateParams | ConfluenceDataSourceUpdateParams,
  >(params: T) {
    return {
      cql: params.cql,
      include_restricted_content: params.include_restricted_content,
      include_archived_content: params.include_archived_content,
      include_attachments: params.include_attachments,
      include_comments: params.include_comments,
      keep_markdown_format: params.keep_markdown_format,
      keep_newlines: params.keep_newlines,
      max_pages: params.max_pages,
      pages_per_request: params.pages_per_request,
    };
  }

  /** Maps Jira-specific parameters: the JQL filter and which issue content to index */
  private static mapJiraDataSourceParams<
    T extends JiraDataSourceCreateParams | JiraDataSourceUpdateParams,
  >(params: T) {
    return {
      jql: params.jql,
      include_attachments: params.include_attachments,
      include_comments: params.include_comments,
    };
  }

  /** Maps Xray-specific parameters, transforming JQL filter configuration */
  private static mapXrayDataSourceParams<
    T extends XrayDataSourceCreateParams | XrayDataSourceUpdateParams,
  >(params: T) {
    return {
      jql: params.jql,
    };
  }

  /** Maps SharePoint-specific configuration parameters */
  private static mapSharePointParams<
    T extends SharePointDataSourceCreateParams | SharePointDataSourceUpdateParams,
  >(params: T) {
    return {
      site_url: params.site_url,
      include_pages: params.include_pages,
      include_documents: params.include_documents,
      include_lists: params.include_lists,
      max_file_size_mb: params.max_file_size_mb,
      files_filter: params.files_filter,
      auth_type: params.auth_type,
      access_token: params.access_token,
      oauth_client_id: params.oauth_client_id,
      oauth_tenant_id: params.oauth_tenant_id,
      embedding_model: params.embedding_model,
      cron_expression: params.cron_expression,
    };
  }

  /** Maps Google Doc specific parameters with proper API naming conventions */
  private static mapGoogleDataSourceParams<
    T extends GoogleDataSourceCreateParams | GoogleDataSourceUpdateParams,
  >(params: T) {
    return {
      googleDoc: params.google_doc,
    };
  }

  /** Maps Git FAQ datasource parameters (link/branch/files_filter) with API naming conventions */
  private static mapGitFaqDataSourceParams<
    T extends GitFaqDataSourceCreateParams | GitFaqDataSourceUpdateParams,
  >(params: T) {
    return {
      link: params.link,
      branch: params.branch,
      files_filter: params.files_filter,
      ...(params.embedding_model !== undefined && { embedding_model: params.embedding_model }),
    };
  }

  /** Maps file upload datasource parameters, handling file reference collections */
  private static mapFileDataSourceParams<
    T extends FileDataSourceCreateParams | FileDataSourceUpdateParams,
  >(params: T) {
    return {
      files: params.files,
    };
  }

  /** Maps code repository specific parameters including indexing strategy and code processing settings */
  private static mapCodeDataSourceParams<
    T extends CodeDataSourceCreateParams | CodeDataSourceUpdateParams,
  >(params: T) {
    return {
      settingId: params.setting_id,
      projectSpaceVisible: params.shared_with_project || false,
      link: params.link,
      branch: params.branch,
      indexType: params.index_type,
      filesFilter: params.files_filter,
      embeddingsModel: params.embeddings_model,
      summarizationModel: params.summarization_model,
      prompt: params.prompt,
      docsGeneration: params.docs_generation || false,
    };
  }

  /** Maps Azure DevOps Wiki-specific configuration parameters */
  private static mapAzureDevOpsWikiParams<
    T extends AzureDevOpsWikiDataSourceCreateParams | AzureDevOpsWikiDataSourceUpdateParams,
  >(params: T) {
    return {
      wiki_query: params.wiki_query,
      organization: params.organization,
      project: params.project,
      wiki_name: params.wiki_name,
    };
  }

  /** Maps Azure DevOps Work Item-specific configuration parameters */
  private static mapAzureDevOpsWorkItemParams<
    T extends AzureDevOpsWorkItemDataSourceCreateParams | AzureDevOpsWorkItemDataSourceUpdateParams,
  >(params: T) {
    return {
      wiql_query: params.wiql_query,
      organization: params.organization,
      project: params.project,
      include_attachments: params.include_attachments,
      include_comments: params.include_comments,
    };
  }

  /** Maps general datasource parameters common across all datasource types with appropriate fallback values */
  private static mapCommonDataSourceParams(params: DataSourceCreateParams) {
    return {
      name: params.name,
      project_name: params.project_name,
      description: params.description,
      project_space_visible: params.shared_with_project || false,
      setting_id: params.setting_id || null,
      type: params.type,
    };
  }

  private static mapCommonUpdateDataSourceParams(params: DataSourceUpdateParams) {
    return omitUndefined({
      name: params.name,
      project_name: params.project_name,
      description: params.description,
      project_space_visible: params.shared_with_project || false,
      setting_id: params.setting_id || null,
      type: params.type,
    });
  }
}
