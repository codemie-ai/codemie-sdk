import { describe, it, expect } from "@jest/globals";
import { DatasourceMapper } from "../../../src/mappers/datasource.mapper";
import type {
  DataSourceResponse,
  DataSourceProcessingInfoResponse,
  DataSourceCreateParams,
  DataSourceUpdateParams,
} from "../../../src/models";
import {
  DataSourceType,
  DataSourceStatus,
  CodeDataSourceType,
} from "../../../src/models/datasource";


describe("DatasourceMapper", () => {
  describe("mapDatasourceResponse", () => {
    it("should correctly map all datasource fields", () => {
      // Arrange
      const apiResponse: DataSourceResponse = {
        id: "ds-123",
        project_name: "test-project",
        repo_name: "test-repo",
        description: "Test datasource",
        index_type: DataSourceType.CODE,
        embeddings_model: "test-model",
        setting_id: "setting-123",
        completed: true,
        date: "2025-01-01",
        created_by: {
          username: "user1",
          name: "User One",
        },
        project_space_visible: true,
        update_date: "2025-01-02",
        text: "error message",
        user_abilities: ["read", "write"],
        processing_info: {
          total_documents: 10,
          skipped_documents: 1,
          total_size_kb: 1000,
          average_file_size_bytes: 1024,
          unique_extensions: [".ts", ".js"],
          filtered_documents: ["test.md"],
          documents_count_key: 9,
        },
        processed_files: ["file1.ts", "file2.js"],
        tokens_usage: {
          input_tokens: 100,
          output_tokens: 50,
        },
        link: "https://github.com/test/repo",
        branch: "main",
        files_filter: "*.ts",
        summarization_model: "test-sum-model",
        prompt: "test prompt",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "ds-123",
        project_name: "test-project",
        name: "test-repo",
        description: "Test datasource",
        type: DataSourceType.CODE,
        embeddings_model: "test-model",
        status: DataSourceStatus.COMPLETED,
        setting_id: "setting-123",
        created_date: "2025-01-01",
        created_by: {
          username: "user1",
          name: "User One",
        },
        shared_with_project: true,
        update_date: "2025-01-02",
        error_message: "error message",
        user_abilities: ["read", "write"],
        processing_info: {
          total_documents_count: 10,
          skipped_documents_count: 1,
          total_size_kb: 1000,
          average_file_size_bytes: 1024,
          unique_extensions: [".ts", ".js"],
          filtered_documents: ["test.md"],
          processed_documents_count: 9,
        },
        processed_documents: ["file1.ts", "file2.js"],
        tokens_usage: {
          input_tokens: 100,
          output_tokens: 50,
        },
        code: {
          branch: "main",
          docsGeneration: false,
          embeddingsModel: "test-model",
          filesFilter: "*.ts",
          indexType: CodeDataSourceType.CODE,
          link: "https://github.com/test/repo",
          projectSpaceVisible: true,
          prompt: "test prompt",
          settingId: "setting-123",
          summarizationModel: "test-sum-model",
        },
      });
    });

    it("should handle undefined fields", () => {
      // Arrange
      const apiResponse: DataSourceResponse = {
        id: "ds-123",
        project_name: "test-project",
        repo_name: "test-repo",
        index_type: DataSourceType.CODE,
        completed: true,
        date: "2025-01-01",
        created_by: {
          username: "user1",
          name: "User One",
        },
        project_space_visible: true,
        update_date: "2025-01-02",
        user_abilities: [],
      };

      // Act
      const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "ds-123",
        project_name: "test-project",
        name: "test-repo",
        type: DataSourceType.CODE,
        status: DataSourceStatus.COMPLETED,
        created_date: "2025-01-01",
        created_by: {
          username: "user1",
          name: "User One",
        },
        shared_with_project: true,
        update_date: "2025-01-02",
        user_abilities: [],
        code: {
          indexType: CodeDataSourceType.CODE,
          projectSpaceVisible: true,
          docsGeneration: false,
        },
      });
    });
  });

  describe("mapDatasourceProcessingInfoResponse", () => {
    it("should correctly map processing info fields", () => {
      // Arrange
      const response: DataSourceProcessingInfoResponse = {
        total_documents: 10,
        skipped_documents: 1,
        total_size_kb: 1000,
        average_file_size_bytes: 1024,
        unique_extensions: [".ts", ".js"],
        filtered_documents: ["test.md"],
        documents_count_key: 9,
      };

      // Act
      const result = DatasourceMapper.mapDatasourceProcessingInfoResponse(response);

      // Assert
      expect(result).toEqual({
        total_documents_count: 10,
        skipped_documents_count: 1,
        total_size_kb: 1000,
        average_file_size_bytes: 1024,
        unique_extensions: [".ts", ".js"],
        filtered_documents: ["test.md"],
        processed_documents_count: 9,
      });
    });

    it("should handle undefined fields", () => {
      // Arrange
      const response: DataSourceProcessingInfoResponse = {
        total_documents: 10,
        documents_count_key: 9,
      };

      // Act
      const result = DatasourceMapper.mapDatasourceProcessingInfoResponse(response);

      // Assert
      expect(result).toEqual({
        total_documents_count: 10,
        processed_documents_count: 9,
      });
    });
  });

  describe("mapDatasourceCreateToDto", () => {
    it("should map common datasource parameters", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "test-source",
        project_name: "test-project",
        description: "Test description",
        shared_with_project: true,
        setting_id: "setting-123",
        type: DataSourceType.FILE,
        files: [
          {
            name: "file1.txt",
            content: "test content",
            mime_type: "text/plain",
          },
        ],
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "test-source",
        project_name: "test-project",
        description: "Test description",
        project_space_visible: true,
        setting_id: "setting-123",
        type: DataSourceType.FILE,
        files: [
          {
            name: "file1.txt",
            content: "test content",
            mime_type: "text/plain",
          },
        ],
      });
    });

    it("should map CODE datasource parameters", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "test-source",
        project_name: "test-project",
        type: DataSourceType.CODE,
        description: "Test code source",
        setting_id: "setting-123",
        shared_with_project: true,
        link: "https://github.com/test/repo",
        branch: "main",
        index_type: CodeDataSourceType.CODE,
        files_filter: "*.ts",
        embeddings_model: "code-model",
        summarization_model: "sum-model",
        prompt: "test prompt",
        docs_generation: true,
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "test-source",
        project_name: "test-project",
        description: "Test code source",
        project_space_visible: true,
        setting_id: "setting-123",
        type: DataSourceType.CODE,
        settingId: "setting-123",
        projectSpaceVisible: true,
        link: "https://github.com/test/repo",
        branch: "main",
        indexType: CodeDataSourceType.CODE,
        filesFilter: "*.ts",
        embeddingsModel: "code-model",
        summarizationModel: "sum-model",
        prompt: "test prompt",
        docsGeneration: true,
      });
    });
  });

  describe("mapDatasourceUpdateToDto", () => {
    it("should map common update parameters", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "updated-source",
        project_name: "test-project",
        description: "Updated description",
        shared_with_project: false,
        setting_id: "setting-456",
        type: DataSourceType.FILE,
        files: [
          {
            name: "updated.txt",
            content: "updated content",
            mime_type: "text/plain",
          },
        ],
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "updated-source",
        project_name: "test-project",
        description: "Updated description",
        project_space_visible: false,
        setting_id: "setting-456",
        type: DataSourceType.FILE,
        files: [
          {
            name: "updated.txt",
            content: "updated content",
            mime_type: "text/plain",
          },
        ],
      });
    });

    it("should map CONFLUENCE datasource update parameters", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "confluence-source",
        project_name: "test-project",
        type: DataSourceType.CONFLUENCE,
        cql: "space=TEST",
        include_restricted_content: true,
        include_archived_content: false,
        include_attachments: true,
        include_comments: true,
        keep_markdown_format: true,
        keep_newlines: true,
        max_pages: 100,
        pages_per_request: 10,
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "confluence-source",
        project_name: "test-project",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.CONFLUENCE,
        cql: "space=TEST",
        include_restricted_content: true,
        include_archived_content: false,
        include_attachments: true,
        include_comments: true,
        keep_markdown_format: true,
        keep_newlines: true,
        max_pages: 100,
        pages_per_request: 10,
      });
    });

    it("should map XRAY datasource create parameters with jql", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "xray-source",
        project_name: "test-project",
        description: "Xray datasource",
        shared_with_project: false,
        setting_id: "setting-123",
        type: DataSourceType.XRAY,
        jql: "project = TEST AND type = Test",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "xray-source",
        project_name: "test-project",
        description: "Xray datasource",
        project_space_visible: false,
        setting_id: "setting-123",
        type: DataSourceType.XRAY,
        jql: "project = TEST AND type = Test",
      });
    });

    it("should map XRAY datasource update parameters with jql", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "xray-source",
        project_name: "test-project",
        type: DataSourceType.XRAY,
        jql: "project = TEST AND type = Test AND status = Pass",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "xray-source",
        project_name: "test-project",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.XRAY,
        jql: "project = TEST AND type = Test AND status = Pass",
      });
    });

    it("should map AZURE_DEVOPS_WIKI datasource create parameters", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "wiki-source",
        project_name: "test-project",
        description: "Azure DevOps Wiki datasource",
        shared_with_project: true,
        setting_id: "setting-123",
        type: DataSourceType.AZURE_DEVOPS_WIKI,
        wiki_query: "my wiki query",
        organization: "my-org",
        project: "my-project",
        wiki_name: "my-wiki",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "wiki-source",
        project_name: "test-project",
        description: "Azure DevOps Wiki datasource",
        project_space_visible: true,
        setting_id: "setting-123",
        type: DataSourceType.AZURE_DEVOPS_WIKI,
        wiki_query: "my wiki query",
        organization: "my-org",
        project: "my-project",
        wiki_name: "my-wiki",
      });
    });

    it("should map AZURE_DEVOPS_WORK_ITEM datasource create parameters", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "workitem-source",
        project_name: "test-project",
        description: "Azure DevOps Work Item datasource",
        shared_with_project: false,
        setting_id: null,
        type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        wiql_query: "SELECT * FROM WorkItems",
        organization: "my-org",
        project: "my-project",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "workitem-source",
        project_name: "test-project",
        description: "Azure DevOps Work Item datasource",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        wiql_query: "SELECT * FROM WorkItems",
        organization: "my-org",
        project: "my-project",
      });
    });

    it("should map AZURE_DEVOPS_WIKI datasource update parameters", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "wiki-source",
        project_name: "test-project",
        type: DataSourceType.AZURE_DEVOPS_WIKI,
        wiki_query: "updated query",
        organization: "new-org",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "wiki-source",
        project_name: "test-project",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.AZURE_DEVOPS_WIKI,
        wiki_query: "updated query",
        organization: "new-org",
      });
    });

    it("should map AZURE_DEVOPS_WORK_ITEM datasource update parameters", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "workitem-source",
        project_name: "test-project",
        type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        wiql_query: "SELECT * FROM WorkItems WHERE State = 'Active'",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "workitem-source",
        project_name: "test-project",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        wiql_query: "SELECT * FROM WorkItems WHERE State = 'Active'",
      });
    });
  });

    it("should map SHAREPOINT datasource create parameters", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "sharepoint-source",
        project_name: "test-project",
        description: "SharePoint datasource",
        shared_with_project: true,
        setting_id: "setting-123",
        type: DataSourceType.SHAREPOINT,
        site_url: "https://tenant.sharepoint.com/sites/mysite",
        include_pages: true,
        include_documents: true,
        include_lists: false,
        max_file_size_mb: 100,
        files_filter: "*.docx\n*.pdf",
        auth_type: "integration",
        embedding_model: "text-embedding-3-small",
        cron_expression: "0 0 * * *",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "sharepoint-source",
        project_name: "test-project",
        description: "SharePoint datasource",
        project_space_visible: true,
        setting_id: "setting-123",
        type: DataSourceType.SHAREPOINT,
        site_url: "https://tenant.sharepoint.com/sites/mysite",
        include_pages: true,
        include_documents: true,
        include_lists: false,
        max_file_size_mb: 100,
        files_filter: "*.docx\n*.pdf",
        auth_type: "integration",
        embedding_model: "text-embedding-3-small",
        cron_expression: "0 0 * * *",
      });
    });

    it("should map SHAREPOINT datasource create parameters with oauth_custom auth", () => {
      // Arrange
      const params: DataSourceCreateParams = {
        name: "sharepoint-oauth",
        project_name: "test-project",
        description: "SharePoint OAuth datasource",
        shared_with_project: false,
        setting_id: null,
        type: DataSourceType.SHAREPOINT,
        site_url: "https://tenant.sharepoint.com/sites/mysite",
        auth_type: "oauth_custom",
        access_token: "access-token",
        oauth_client_id: "my-client-id",
        oauth_tenant_id: "my-tenant-id",
      };

      // Act
      const result = DatasourceMapper.mapDatasourceCreateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "sharepoint-oauth",
        project_name: "test-project",
        description: "SharePoint OAuth datasource",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.SHAREPOINT,
        site_url: "https://tenant.sharepoint.com/sites/mysite",
        auth_type: "oauth_custom",
        access_token: "access-token",
        oauth_client_id: "my-client-id",
        oauth_tenant_id: "my-tenant-id",
      });
    });

    it("should map SHAREPOINT datasource update parameters", () => {
      // Arrange
      const params: DataSourceUpdateParams = {
        name: "sharepoint-source",
        project_name: "test-project",
        type: DataSourceType.SHAREPOINT,
        include_lists: true,
        max_file_size_mb: 200,
      };

      // Act
      const result = DatasourceMapper.mapDatasourceUpdateToDto(params);

      // Assert
      expect(result).toEqual({
        name: "sharepoint-source",
        project_name: "test-project",
        project_space_visible: false,
        setting_id: null,
        type: DataSourceType.SHAREPOINT,
        include_lists: true,
        max_file_size_mb: 200,
      });
    });

  describe("mapDatasourceResponse (Azure DevOps types)", () => {
    it("should map AZURE_DEVOPS_WIKI response with nested config", () => {
      // Arrange
      const apiResponse: DataSourceResponse = {
        id: "ds-wiki-1",
        project_name: "test-project",
        repo_name: "my-wiki-source",
        index_type: DataSourceType.AZURE_DEVOPS_WIKI,
        completed: true,
        date: "2025-01-01",
        created_by: { username: "user1", name: "User One" },
        project_space_visible: false,
        update_date: "2025-01-02",
        user_abilities: ["read"],
        azure_devops_wiki: {
          wiki_query: "my query",
          organization: "my-org",
          project: "my-project",
          wiki_name: "my-wiki",
        },
      };

      // Act
      const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "ds-wiki-1",
        project_name: "test-project",
        name: "my-wiki-source",
        type: DataSourceType.AZURE_DEVOPS_WIKI,
        status: DataSourceStatus.COMPLETED,
        created_date: "2025-01-01",
        created_by: { username: "user1", name: "User One" },
        shared_with_project: false,
        update_date: "2025-01-02",
        user_abilities: ["read"],
        azure_devops_wiki: {
          wiki_query: "my query",
          organization: "my-org",
          project: "my-project",
          wiki_name: "my-wiki",
        },
      });
    });

    it("should map AZURE_DEVOPS_WORK_ITEM response with nested config", () => {
      // Arrange
      const apiResponse: DataSourceResponse = {
        id: "ds-wi-1",
        project_name: "test-project",
        repo_name: "my-workitem-source",
        index_type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        completed: false,
        is_fetching: true,
        date: "2025-02-01",
        created_by: { username: "user2", name: "User Two" },
        project_space_visible: true,
        update_date: "2025-02-02",
        user_abilities: ["read", "write"],
        azure_devops_work_item: {
          wiql_query: "SELECT * FROM WorkItems",
          organization: "my-org",
          project: "my-project",
        },
      };

      // Act
      const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "ds-wi-1",
        project_name: "test-project",
        name: "my-workitem-source",
        type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
        status: DataSourceStatus.FETCHING,
        created_date: "2025-02-01",
        created_by: { username: "user2", name: "User Two" },
        shared_with_project: true,
        update_date: "2025-02-02",
        user_abilities: ["read", "write"],
        azure_devops_work_item: {
          wiql_query: "SELECT * FROM WorkItems",
          organization: "my-org",
          project: "my-project",
        },
      });
    });

    it("should map SHAREPOINT response with nested config", () => {
      // Arrange
      const apiResponse: DataSourceResponse = {
        id: "ds-sp-1",
        project_name: "test-project",
        repo_name: "my-sharepoint-source",
        index_type: DataSourceType.SHAREPOINT,
        completed: true,
        date: "2025-03-01",
        created_by: { username: "user3", name: "User Three" },
        project_space_visible: true,
        update_date: "2025-03-02",
        user_abilities: ["read", "write"],
        sharepoint: {
          site_url: "https://tenant.sharepoint.com/sites/mysite",
          include_pages: true,
          include_documents: true,
          include_lists: false,
          max_file_size_mb: 50,
          files_filter: "*.docx",
          auth_type: "integration",
        },
      };

      // Act
      const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

      // Assert
      expect(result).toEqual({
        id: "ds-sp-1",
        project_name: "test-project",
        name: "my-sharepoint-source",
        type: DataSourceType.SHAREPOINT,
        status: DataSourceStatus.COMPLETED,
        created_date: "2025-03-01",
        created_by: { username: "user3", name: "User Three" },
        shared_with_project: true,
        update_date: "2025-03-02",
        user_abilities: ["read", "write"],
        sharepoint: {
          site_url: "https://tenant.sharepoint.com/sites/mysite",
          include_pages: true,
          include_documents: true,
          include_lists: false,
          max_file_size_mb: 50,
          files_filter: "*.docx",
          auth_type: "integration",
        },
      });
    });
  });
});

describe('DatasourceMapper FAQ (knowledge_base_git_faq)', () => {
  it('maps FAQ create params without an implicit files_filter (backend scans the whole repo)', () => {
    const dto = DatasourceMapper.mapDatasourceCreateToDto({
      type: DataSourceType.GIT_FAQ,
      name: 'team_faq',
      project_name: 'proj',
      description: 'FAQ',
      link: 'https://git.example.com/docs.git',
      branch: 'main',
    } as any);

    expect((dto as any).link).toBe('https://git.example.com/docs.git');
    expect((dto as any).branch).toBe('main');
    expect((dto as any).files_filter).toBeUndefined();
  });

  it('keeps an explicit files_filter (same gitignore-style mechanism as the code datasource)', () => {
    const dto = DatasourceMapper.mapDatasourceCreateToDto({
      type: DataSourceType.GIT_FAQ,
      name: 'team_faq',
      project_name: 'proj',
      description: 'FAQ',
      link: 'https://x.git',
      branch: 'main',
      files_filter: 'docs/**/*.md',
    } as any);

    expect((dto as any).files_filter).toBe('docs/**/*.md');
  });

  it('maps FAQ update params without implicit source fields', () => {
    const dto = DatasourceMapper.mapDatasourceUpdateToDto({
      type: DataSourceType.GIT_FAQ,
      name: 'team_faq',
      project_name: 'proj',
      description: 'new description',
    } as any);

    expect((dto as any).files_filter).toBeUndefined();
    expect((dto as any).link).toBeUndefined();
    expect((dto as any).branch).toBeUndefined();
  });

  it('extracts FAQ response fields', () => {
    const model = DatasourceMapper.mapDatasourceResponse({
      id: '1',
      project_name: 'proj',
      repo_name: 'team_faq',
      index_type: 'knowledge_base_git_faq',
      link: 'https://x.git',
      branch: 'main',
      files_filter: 'docs/**/*.md',
    } as any);

    expect((model as any).git_faq).toEqual({
      link: 'https://x.git',
      branch: 'main',
      files_filter: 'docs/**/*.md',
    });
  });
});

describe("DatasourceMapper include_attachments / include_comments", () => {
  const common = {
    name: "ds",
    project_name: "test-project",
    description: "d",
    shared_with_project: false,
    setting_id: null,
  };

  it("sends both flags on JIRA create", () => {
    const params: DataSourceCreateParams = {
      ...common,
      type: DataSourceType.JIRA,
      jql: "project = TEST",
      include_attachments: true,
      include_comments: false,
    };

    const body = JSON.parse(JSON.stringify(DatasourceMapper.mapDatasourceCreateToDto(params)));

    expect(body).toMatchObject({ jql: "project = TEST", include_attachments: true, include_comments: false });
  });

  it("omits unset flags on JIRA create so the backend default applies", () => {
    const params: DataSourceCreateParams = { ...common, type: DataSourceType.JIRA, jql: "project = TEST" };

    const body = JSON.parse(JSON.stringify(DatasourceMapper.mapDatasourceCreateToDto(params)));

    expect(body).not.toHaveProperty("include_attachments");
    expect(body).not.toHaveProperty("include_comments");
  });

  it("sends only the changed flag on JIRA update so the other keeps its stored value", () => {
    const params: DataSourceUpdateParams = {
      name: "ds",
      project_name: "test-project",
      type: DataSourceType.JIRA,
      include_comments: false,
    };

    const body = JSON.parse(JSON.stringify(DatasourceMapper.mapDatasourceUpdateToDto(params)));

    expect(body.include_comments).toBe(false);
    expect(body).not.toHaveProperty("include_attachments");
  });

  it("sends both flags on AZURE_DEVOPS_WORK_ITEM create", () => {
    const params: DataSourceCreateParams = {
      ...common,
      type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
      include_attachments: false,
      include_comments: true,
    };

    const body = JSON.parse(JSON.stringify(DatasourceMapper.mapDatasourceCreateToDto(params)));

    expect(body).toMatchObject({ include_attachments: false, include_comments: true });
  });

  it("omits unset flags on AZURE_DEVOPS_WORK_ITEM update so the stored values are kept", () => {
    const params: DataSourceUpdateParams = {
      name: "ds",
      project_name: "test-project",
      type: DataSourceType.AZURE_DEVOPS_WORK_ITEM,
      wiql_query: "SELECT * FROM WorkItems",
    };

    const body = JSON.parse(JSON.stringify(DatasourceMapper.mapDatasourceUpdateToDto(params)));

    expect(body).not.toHaveProperty("include_attachments");
    expect(body).not.toHaveProperty("include_comments");
  });

  it("does not add the flags to XRAY", () => {
    const params: DataSourceCreateParams = { ...common, type: DataSourceType.XRAY, jql: "project = TEST" };

    const body = DatasourceMapper.mapDatasourceCreateToDto(params);

    expect(Object.keys(body)).not.toContain("include_attachments");
    expect(Object.keys(body)).not.toContain("include_comments");
  });

  it("keeps the stored flags in the JIRA response", () => {
    const apiResponse: DataSourceResponse = {
      id: "ds-jira-1",
      project_name: "test-project",
      repo_name: "jira-source",
      index_type: DataSourceType.JIRA,
      completed: true,
      date: "2025-02-01",
      created_by: { username: "user", name: "User" },
      project_space_visible: false,
      update_date: "2025-02-02",
      user_abilities: ["read"],
      jira: { jql: "project = TEST", include_attachments: true, include_comments: false },
    };

    const result = DatasourceMapper.mapDatasourceResponse(apiResponse);

    expect(result.jira).toEqual({ jql: "project = TEST", include_attachments: true, include_comments: false });
  });
});
