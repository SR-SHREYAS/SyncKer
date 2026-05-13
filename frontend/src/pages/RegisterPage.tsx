import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { Layout } from "../components/Layout";
import { PageHeader } from "../components/PageHeader";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, registerError } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      await register({
        email,
        username,
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
        eyebrow="Registration"
        title="Create your SyncKer account"
        subtitle="This branch keeps signup simple so we can move quickly into the working dashboard."
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
          <span>Username</span>
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Choose a username"
            minLength={3}
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
            minLength={8}
            disabled={isSubmitting}
            required
          />
        </label>

        {registerError ? <p className="form-error">{registerError}</p> : null}

        <button className="primary-button wide-button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="footnote">
        Already registered? <Link to="/login">Go to login</Link>.
      </p>
    </Layout>
  );
}
