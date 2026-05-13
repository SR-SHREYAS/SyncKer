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

  let response: Response;

  try {
    response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
      method,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(
      "Network error. Please check your connection and backend server.",
      0,
    );
  }

  if (!response.ok) {
    const errorPayload = (await tryReadJson(response)) as ErrorPayload | null;
    const message =
      errorPayload?.detail ||
      errorPayload?.message ||
      "Request failed. Please try again.";

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const responseText = await response.text();

  if (!responseText.trim()) {
    return undefined as T;
  }

  try {
    return JSON.parse(responseText) as T;
  } catch {
    throw new ApiError(
      "Server returned an unexpected response format.",
      response.status,
    );
  }
}

async function tryReadJson(response: Response): Promise<unknown | null> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
