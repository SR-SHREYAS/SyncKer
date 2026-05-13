import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../app/AuthContext";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isInitializing } = useAuth();

  if (isInitializing) {
    return (
      <main className="screen shell-screen">
        <section className="panel status-panel">
          <p className="eyebrow">SyncKer</p>
          <h1>Loading your workspace</h1>
          <p className="muted">
            We are checking your session before opening the dashboard.
          </p>
        </section>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
