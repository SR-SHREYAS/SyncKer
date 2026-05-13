import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { ApiError } from "../lib/api";
import { clearStoredAccessToken, getStoredAccessToken, storeAccessToken } from "../lib/storage";
import { loginUser, registerUser } from "../services/authService";
import { getCurrentUser } from "../services/userService";
import type { LoginRequest, RegisterRequest } from "../types/auth";
import type { User } from "../types/user";

type AuthContextValue = {
  currentUser: User | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  loginError: string | null;
  registerError: string | null;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);

  useEffect(() => {
    const accessToken = getStoredAccessToken();

    if (!accessToken) {
      setIsInitializing(false);
      return;
    }

    void getCurrentUser()
      .then((user) => {
        startTransition(() => {
          setCurrentUser(user);
        });
      })
      .catch(() => {
        clearStoredAccessToken();
      })
      .finally(() => {
        setIsInitializing(false);
      });
  }, []);

  async function login(payload: LoginRequest): Promise<void> {
    setLoginError(null);

    try {
      const authResponse = await loginUser(payload);
      storeAccessToken(authResponse.token.access_token);
      const user = await getCurrentUser();

      startTransition(() => {
        setCurrentUser(user);
      });
    } catch (error) {
      clearStoredAccessToken();
      setLoginError(getErrorMessage(error));
      throw error;
    }
  }

  async function register(payload: RegisterRequest): Promise<void> {
    setRegisterError(null);

    try {
      const authResponse = await registerUser(payload);
      storeAccessToken(authResponse.token.access_token);
      const user = await getCurrentUser();

      startTransition(() => {
        setCurrentUser(user);
      });
    } catch (error) {
      clearStoredAccessToken();
      setRegisterError(getErrorMessage(error));
      throw error;
    }
  }

  function logout(): void {
    clearStoredAccessToken();

    startTransition(() => {
      setCurrentUser(null);
      setLoginError(null);
      setRegisterError(null);
    });
  }

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: currentUser !== null,
        isInitializing,
        loginError,
        registerError,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
