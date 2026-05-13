import { apiRequest } from "../lib/api";
import type { User } from "../types/user";

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/users/me");
}
