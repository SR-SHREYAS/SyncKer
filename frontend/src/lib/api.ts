import { appConfig } from "./config";
import { getStoredAccessToken } from "./storage";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: HeadersInit;
};

type ErrorPayload = {
  detail?: string;
  message?: string;
};

export class ApiError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

export async function apiRequest<T>(
  path: string,
  { method = "GET", body, headers }: RequestOptions = {},
): Promise<T> {
  const accessToken = getStoredAccessToken();
  const requestHeaders = new Headers(headers);

  if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (accessToken) {
    requestHeaders.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    method,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorPayload = (await tryReadJson(response)) as ErrorPayload | null;
    const message =
      errorPayload?.detail ||
      errorPayload?.message ||
      "Request failed. Please try again.";

    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

async function tryReadJson(response: Response): Promise<unknown | null> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
