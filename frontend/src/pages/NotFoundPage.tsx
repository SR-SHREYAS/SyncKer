import { Link } from "react-router-dom";

import { AuthStatusShell } from "../components/AuthStatusShell";

export function NotFoundPage() {
  return (
    <AuthStatusShell
      title="Page not found"
      description="The page you tried to open does not exist in this frontend build."
      actions={
        <>
          <Link className="primary-button" to="/">
            Back to home
          </Link>
          <Link className="secondary-button" to="/dashboard">
            Go to dashboard
          </Link>
        </>
      }
    />
  );
}
