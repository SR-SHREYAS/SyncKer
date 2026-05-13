import { Link, Navigate } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../app/AuthContext";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { initError, isAuthenticated, isInitializing } = useAuth();

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

  if (initError && !isAuthenticated) {
    return (
      <main className="screen shell-screen">
        <section className="panel status-panel">
          <p className="eyebrow">SyncKer</p>
          <h1>We could not restore your session</h1>
          <p className="muted">
            {initError}
          </p>
          <div className="status-actions">
            <Link className="primary-button" to="/login">
              Go to login
            </Link>
            <Link className="secondary-button" to="/">
              Back to home
            </Link>
          </div>
        </section>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
