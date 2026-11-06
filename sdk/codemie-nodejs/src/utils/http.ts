import { Agent } from "node:https";
import axios from "axios";
import type { AxiosError, AxiosInstance, AxiosResponse } from "axios/index";
import type FormData from "form-data";
import { ApiError, NotFoundError } from "../exceptions";
import type { AuthConfig } from "../models/common";

export interface ApiResponse<T> {
  data: T;
}

/**
 * Convert cookies object to cookie string format.
 * Example: {key1: "value1", key2: "value2"} => "key1=value1; key2=value2"
 */
export function formatCookies(cookies: Record<string, string>): string {
  return Object.entries(cookies)
    .map(([key, value]) => `${key}=${value}`)
    .join("; ");
}

export class ApiRequestHandler {
  private client: AxiosInstance;

  constructor(config: AuthConfig) {
    const { apiDomain, token, verifySSL = true, cookies = {}, tokenGetter } = config;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Use Cookie header if cookies are provided, otherwise use Bearer token
    if (Object.keys(cookies).length > 0) {
      headers.Cookie = formatCookies(cookies);
    } else if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    this.client = axios.create({
      baseURL: apiDomain.replace(/\/$/, ""), // Remove trailing slash
      validateStatus: (status: number) => status < 400,
      headers,
      httpsAgent: new Agent({
        rejectUnauthorized: verifySSL,
      }),
    });

    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => this.processFailedResponse(error),
    );

    if (tokenGetter) {
      this.client.interceptors.request.use(async (requestConfig) => {
        const freshToken = await tokenGetter();
        requestConfig.headers.Authorization = `Bearer ${freshToken}`;
        return requestConfig;
      });
    }
  }

  private async request<T>(
    method: "get" | "post" | "put" | "patch" | "delete",
    path: string,
    config: Record<string, unknown> = {},
  ): Promise<T> {
    const response = await this.client.request<T>({
      method,
      url: path,
      ...config,
    });
    return response.data;
  }

  /**
   * Merge extra headers into the request (used for X-* propagation)
   */
  private withHeaders(config: Record<string, unknown> = {}, extraHeaders?: Record<string, string>) {
    if (!extraHeaders || Object.keys(extraHeaders).length === 0) return config;
    const headers = (config.headers as Record<string, string> | undefined) ?? {};
    return { ...config, headers: { ...headers, ...extraHeaders } };
  }

  async get<T>(
    path: string,
    params?: Record<string, unknown>,
    config: Record<string, unknown> = {},
    extraHeaders?: Record<string, string>,
  ): Promise<T> {
    return this.request<T>("get", path, this.withHeaders({ ...config, params }, extraHeaders));
  }

  async post<T>(
    path: string,
    data?: unknown,
    config: Record<string, unknown> = {},
    extraHeaders?: Record<string, string>,
  ): Promise<T> {
    return this.request<T>("post", path, this.withHeaders({ ...config, data }, extraHeaders));
  }

  async put<T>(
    path: string,
    data?: unknown,
    config: Record<string, unknown> = {},
    extraHeaders?: Record<string, string>,
  ): Promise<T> {
    return this.request<T>("put", path, this.withHeaders({ ...config, data }, extraHeaders));
  }

  async patch<T>(
    path: string,
    data?: unknown,
    config: Record<string, unknown> = {},
    extraHeaders?: Record<string, string>,
  ): Promise<T> {
    return this.request<T>("patch", path, this.withHeaders({ ...config, data }, extraHeaders));
  }

  async postMultipart<T>(
    url: string,
    formData: FormData,
    params?: Record<string, unknown>,
  ): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      params,
    });
    return response.data;
  }

  async delete<T>(path: string, config: Record<string, unknown> = {}): Promise<T> {
    return this.request<T>("delete", path, config);
  }

  async stream(
    path: string,
    data?: unknown,
    config: Record<string, unknown> = {},
  ): Promise<AxiosResponse> {
    return this.client.post(path, data, {
      ...config,
      responseType: "stream",
    });
  }

  private processFailedResponse(error: AxiosError): void {
    const response = error.response;
    const status = response?.status || 500;

    const data = (response?.data || {}) as {
      error?: { message?: string; detail?: string; help?: string; details?: string };
    };

    if (status === 404) {
      throw new NotFoundError("Resource", "unknown");
    }

    if (status === 422) {
      // Validation error returns different structure (details instead of detail)
      const errorMessage = [
        data.error?.message,
        data.error?.help,
        JSON.stringify(data.error?.details ?? {}),
      ]
        .filter(Boolean)
        .join(". ");
      throw new ApiError(errorMessage || "Validation error", status, data);
    }

    const errorMessage = [data.error?.message, data.error?.detail, data.error?.help]
      .filter(Boolean)
      .join(". ");

    throw new ApiError(errorMessage || `HTTP ${status} error`, status, data);
  }
}
