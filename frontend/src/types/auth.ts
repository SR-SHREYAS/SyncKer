import type { UserIdentity } from "./user";

export type AuthUser = UserIdentity;

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
};

export type AuthResponse = {
  user: AuthUser;
  token: TokenResponse;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = {
  email: string;
  username: string;
  password: string;
};
