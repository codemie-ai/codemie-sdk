/** Useful diagnostic context, excluding request headers, body and query values. */
export interface ApiErrorRequestContext {
  method?: string;
  path?: string;
  requestId?: string;
  code?: string;
}

export class CodeMieError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CodeMieError";
  }
}

export class ApiError extends CodeMieError {
  statusCode?: number;
  response?: unknown;
  request?: ApiErrorRequestContext;

  constructor(message: string, statusCode?: number, response?: unknown, request?: ApiErrorRequestContext) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.response = response;
    this.request = request;
  }
}

export class NotFoundError extends ApiError {
  constructor(
    resourceType: string,
    resourceId: string,
    details?: { message?: string; response?: unknown; request?: ApiErrorRequestContext },
  ) {
    super(
      details?.message || `${resourceType} with ${resourceId} not found`,
      404,
      details?.response,
      details?.request,
    );
    this.name = "NotFoundError";
  }
}
