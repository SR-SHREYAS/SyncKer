import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { AuthStatusShell } from "../components/AuthStatusShell";
import { Layout } from "../components/Layout";
import { PageHeader } from "../components/PageHeader";

export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, isInitializing, login, loginError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const redirectPath =
    (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ||
    "/dashboard";

  if (isInitializing) {
    return (
      <AuthStatusShell
        title="Checking your session"
        description="We are making sure you are routed to the right workspace entry point."
      />
    );
  }

  if (isAuthenticated) {
    return <Navigate to={redirectPath} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const isSuccessful = await login({
        email,
        password,
      });

      if (isSuccessful) {
        navigate(redirectPath, { replace: true });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Layout>
      <PageHeader
        eyebrow="Authentication"
        title="Sign in to your workspace"
        subtitle="Use your backend account credentials to open the dashboard shell."
      />

      <form className="stack-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            disabled={isSubmitting}
            required
          />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Minimum 8 characters"
            disabled={isSubmitting}
            required
          />
        </label>

        {loginError ? <p className="form-error">{loginError}</p> : null}

        <button className="primary-button wide-button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="footnote">
        No account yet? <Link to="/register">Create one here</Link>.
      </p>
    </Layout>
  );
}
