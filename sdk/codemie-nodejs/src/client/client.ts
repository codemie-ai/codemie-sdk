import { KeycloakCredentials } from "../auth/credentials";
import type { AuthConfig } from "../models/common";
import { AnalyticsService } from "../services/analytics";
import { AssistantService } from "../services/assistant";
import { ConversationService } from "../services/conversation";
import { DatasourceService } from "../services/datasource";
import { FileService } from "../services/files";
import { IntegrationService } from "../services/integration";
import { LLMService } from "../services/llm";
import { ProjectService } from "../services/project";
import { SkillService } from "../services/skill";
import { TaskService } from "../services/task";
import { UserService } from "../services/user";
import { CategoryService } from "../services/category";
import { WorkflowService } from "../services/workflow";

export interface CodeMieClientConfig {
  auth_server_url?: string;
  auth_realm_name?: string;
  codemie_api_domain: string;
  auth_client_id?: string;
  auth_client_secret?: string;
  username?: string;
  password?: string;
  external_token?: string;
  external_idp?: string;
  cookies?: Record<string, string>;
  verify_ssl?: boolean;
  jwt_token?: string;
}

export class CodeMieClient {
  private auth: KeycloakCredentials | null = null;
  private token: string | null = null;
  private cookies: Record<string, string>;
  private apiDomain: string;
  private verifySSL: boolean;
  private useCookieAuth: boolean;
  private _isJwtAuth = false;
  private _jwtToken: string | null = null;

  // Service instances
  private _analytics: AnalyticsService;
  private _assistants: AssistantService;
  private _conversations: ConversationService;
  private _datasources: DatasourceService;
  private _files: FileService;
  private _integrations: IntegrationService;
  private _llms: LLMService;
  private _skills: SkillService;
  private _projects: ProjectService;
  private _tasks: TaskService;
  private _users: UserService;
  private _categories: CategoryService;
  private _workflows: WorkflowService;

  constructor(config: CodeMieClientConfig) {
    const {
      auth_server_url,
      auth_realm_name,
      codemie_api_domain,
      auth_client_id,
      auth_client_secret,
      username,
      password,
      external_token,
      external_idp,
      cookies,
      verify_ssl = true,
      jwt_token,
    } = config;

    this.apiDomain = codemie_api_domain.replace(/\/$/, "");
    this.verifySSL = verify_ssl;
    this.cookies = cookies || {};
    this.useCookieAuth = !!cookies && Object.keys(cookies).length > 0;
    this._isJwtAuth = !!jwt_token;

    if (this._isJwtAuth) {
      this._jwtToken = jwt_token ?? null;
    } else if (!this.useCookieAuth) {
      if (!auth_server_url || !auth_realm_name) {
        throw new Error(
          "auth_server_url and auth_realm_name are required when not using cookie authentication",
        );
      }

      this.auth = new KeycloakCredentials({
        serverUrl: auth_server_url,
        realmName: auth_realm_name,
        clientId: auth_client_id,
        clientSecret: auth_client_secret,
        username: username,
        password: password,
        externalToken: external_token,
        externalIdp: external_idp,
        verifySSL: verify_ssl,
      });
      this.token = "";
    }

    let tokenGetter: AuthConfig["tokenGetter"];
    if (this._isJwtAuth) {
      tokenGetter = () => {
        if (!this._jwtToken) throw new Error("JWT token not configured");
        return Promise.resolve(this._jwtToken);
      };
    } else {
      // biome-ignore lint/style/noNonNullAssertion: auth is non-null here, guarded by ternary
      tokenGetter = this.auth ? () => this.auth!.getToken() : null;
    }

    const authConfig: AuthConfig = {
      apiDomain: this.apiDomain,
      token: this.token,
      verifySSL: this.verifySSL,
      cookies: this.cookies,
      tokenGetter,
    };

    this._analytics = new AnalyticsService(authConfig);
    this._assistants = new AssistantService(authConfig);
    this._conversations = new ConversationService(authConfig);
    this._datasources = new DatasourceService(authConfig);
    this._files = new FileService(authConfig);
    this._integrations = new IntegrationService(authConfig);
    this._llms = new LLMService(authConfig);
    this._tasks = new TaskService(authConfig);
    this._skills = new SkillService(authConfig);
    this._projects = new ProjectService(authConfig);
    this._users = new UserService(authConfig);
    this._categories = new CategoryService(authConfig);
    this._workflows = new WorkflowService(authConfig);
  }

  /**
   * Get the AnalyticsService instance.
   */
  get analytics(): AnalyticsService {
    return this._analytics;
  }

  /**
   * Get the AssistantService instance.
   */
  get assistants(): AssistantService {
    return this._assistants;
  }

  /**
   * Get the ConversationService instance.
   */
  get conversations(): ConversationService {
    return this._conversations;
  }

  /**
   * Get the LLMService instance.
   */
  get llms(): LLMService {
    return this._llms;
  }

  /**
   * Get the IntegrationService instance.
   */
  get integrations(): IntegrationService {
    return this._integrations;
  }

  /**
   * Get the TaskService instance.
   */
  get tasks(): TaskService {
    return this._tasks;
  }

  /**
   * Get the UserService instance.
   */
  get users(): UserService {
    return this._users;
  }

  /**
   * Get the DatasourceService instance.
   */
  get datasources(): DatasourceService {
    return this._datasources;
  }

  /**
   * Get the FileService instance.
   */
  get files(): FileService {
    return this._files;
  }

  /**
   * Get the CategoryService instance.
   */
  get categories(): CategoryService {
    return this._categories;
  }

  /**
   * Get the ProjectService instance.
   */
  get projects(): ProjectService {
    return this._projects;
  }

  /**
   * Get the SkillService instance.
   */
  get skills(): SkillService {
    return this._skills;
  }

  /**
   * Get the WorkflowService instance.
   */
  get workflows(): WorkflowService {
    return this._workflows;
  }

  /**
   * Initialize the client by obtaining the initial token.
   * This should be called after creating the client instance.
   * When using cookie-based or JWT token authentication, this is a no-op.
   */
  async initialize(): Promise<void> {
    if (this.useCookieAuth || this._isJwtAuth) {
      return;
    }

    if (!this.auth) {
      throw new Error("Authentication not configured");
    }

    this.token = await this.auth.getToken();
    await this.refreshServices();
  }

  /**
   * Get the current access token or fetch a new one if not available.
   * Returns null when using cookie-based authentication.
   */
  async getToken(): Promise<string | null> {
    if (this.useCookieAuth) {
      return null;
    }

    if (this._isJwtAuth) {
      return this._jwtToken;
    }

    if (!this.auth) {
      throw new Error("Authentication not configured");
    }

    if (!this.token) {
      this.token = await this.auth.getToken();
      await this.refreshServices();
    }
    return this.token;
  }

  /**
   * Force token refresh and update all services with the new token.
   * Throws an error when using cookie-based authentication.
   * Returns the static token unchanged when using JWT authentication.
   */
  async refreshToken(): Promise<string> {
    if (this.useCookieAuth) {
      throw new Error("Token refresh is not supported with cookie-based authentication");
    }

    if (this._isJwtAuth) {
      if (!this._jwtToken) throw new Error("JWT token not configured");
      return this._jwtToken;
    }

    if (!this.auth) {
      throw new Error("Authentication not configured");
    }

    this.auth.clearCache();
    this.token = await this.auth.getToken();
    await this.refreshServices();
    return this.token;
  }

  /**
   * Reinitialize all services with the current token or cookies.
   */
  private async refreshServices(): Promise<void> {
    if (this.useCookieAuth || this._isJwtAuth) {
      return;
    }

    if (!this.token) {
      throw new Error("Token not available");
    }

    const authConfig: AuthConfig = {
      apiDomain: this.apiDomain,
      token: this.token,
      verifySSL: this.verifySSL,
      cookies: this.cookies,
      // biome-ignore lint/style/noNonNullAssertion: auth is non-null here, guarded by ternary
      tokenGetter: this.auth ? () => this.auth!.getToken() : null,
    };

    this._analytics = new AnalyticsService(authConfig);
    this._assistants = new AssistantService(authConfig);
    this._conversations = new ConversationService(authConfig);
    this._datasources = new DatasourceService(authConfig);
    this._files = new FileService(authConfig);
    this._integrations = new IntegrationService(authConfig);
    this._llms = new LLMService(authConfig);
    this._skills = new SkillService(authConfig);
    this._projects = new ProjectService(authConfig);
    this._tasks = new TaskService(authConfig);
    this._users = new UserService(authConfig);
    this._categories = new CategoryService(authConfig);
    this._workflows = new WorkflowService(authConfig);
  }
}
