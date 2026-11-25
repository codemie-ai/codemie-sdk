import type { HeadroomSavings } from "./headroom";

export interface TokensUsage {
  input_tokens?: number;
  output_tokens?: number;
  money_spent?: number;
  headroom?: HeadroomSavings;
}

export interface BaseUser {
  id?: string;
  username: string;
  name: string;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export type SortOrder = "asc" | "desc";

/** API specification not defined in the OpenAPI spec. */
export type AnyJson = Record<string, unknown>;

/**
 * Authentication configuration for API requests.
 * Used by ApiRequestHandler and all service classes.
 */
export interface AuthConfig {
  apiDomain: string;
  token?: string | null;
  verifySSL?: boolean;
  cookies?: Record<string, string>;
  tokenGetter?: (() => Promise<string>) | null;
}
