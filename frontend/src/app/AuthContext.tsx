import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";

import { ApiError } from "../lib/api";
import { clearStoredAccessToken, getStoredAccessToken, storeAccessToken } from "../lib/storage";
import { loginUser, registerUser } from "../services/authService";
import { getCurrentUser } from "../services/userService";
import type { AuthResponse, LoginRequest, RegisterRequest } from "../types/auth";
import type { UserIdentity } from "../types/user";

type AuthContextValue = {
  currentUser: UserIdentity | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  initError: string | null;
  loginError: string | null;
  registerError: string | null;
  login: (payload: LoginRequest) => Promise<boolean>;
  register: (payload: RegisterRequest) => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
type ErrorStateSetter = Dispatch<SetStateAction<string | null>>;

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function isAuthBootstrapFailure(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.statusCode === 401 || error.statusCode === 403)
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<UserIdentity | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
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
          setInitError(null);
        });
      })
      .catch((error: unknown) => {
        console.error("Failed to initialize current user during auth bootstrap", error);

        if (isAuthBootstrapFailure(error)) {
          clearStoredAccessToken();
        }

        startTransition(() => {
          if (isAuthBootstrapFailure(error)) {
            setCurrentUser(null);
          }
          setInitError(getErrorMessage(error));
        });
      })
      .finally(() => {
        setIsInitializing(false);
      });
  }, []);

  async function completeAuthenticatedSession(authResponse: AuthResponse): Promise<void> {
    storeAccessToken(authResponse.token.access_token);

    startTransition(() => {
      setInitError(null);
      setCurrentUser(authResponse.user);
    });
  }

  async function runAuthFlow(
    requestAuth: () => Promise<AuthResponse>,
    setError: ErrorStateSetter,
  ): Promise<boolean> {
    setError(null);

    try {
      const authResponse = await requestAuth();
      await completeAuthenticatedSession(authResponse);
      return true;
    } catch (error) {
      if (isAuthBootstrapFailure(error)) {
        clearStoredAccessToken();
      }
      setError(getErrorMessage(error));
      return false;
    }
  }

  async function login(payload: LoginRequest): Promise<boolean> {
    return runAuthFlow(() => loginUser(payload), setLoginError);
  }

  async function register(payload: RegisterRequest): Promise<boolean> {
    return runAuthFlow(() => registerUser(payload), setRegisterError);
  }

  function logout(): void {
    clearStoredAccessToken();

    startTransition(() => {
      setCurrentUser(null);
      setInitError(null);
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
        initError,
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
