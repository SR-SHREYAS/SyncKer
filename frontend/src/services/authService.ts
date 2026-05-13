import { apiRequest } from "../lib/api";
import type { AuthResponse, LoginRequest, RegisterRequest } from "../types/auth";

export function loginUser(payload: LoginRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function registerUser(payload: RegisterRequest): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: payload,
  });
}
