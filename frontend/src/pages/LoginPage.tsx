import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { Layout } from "../components/Layout";
import { PageHeader } from "../components/PageHeader";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, loginError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      await login({
        email,
        password,
      });

      navigate("/dashboard");
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
