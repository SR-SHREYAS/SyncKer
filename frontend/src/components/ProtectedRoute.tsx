import { Link, Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../app/AuthContext";
import { AuthStatusShell } from "./AuthStatusShell";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { initError, isAuthenticated, isInitializing } = useAuth();

  if (isInitializing) {
    return (
      <AuthStatusShell
        title="Loading your workspace"
        description="We are checking your session before opening the dashboard."
      />
    );
  }

  if (initError && !isAuthenticated) {
    return (
      <AuthStatusShell
        title="We could not restore your session"
        description={initError}
        actions={
          <>
            <Link className="primary-button" to="/login">
              Go to login
            </Link>
            <Link className="secondary-button" to="/">
              Back to home
            </Link>
          </>
        }
      />
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}
