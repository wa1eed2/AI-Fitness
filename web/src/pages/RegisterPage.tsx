import {
  FormEvent,
  useState
} from "react";

import {
  Link,
  Navigate,
  useNavigate
} from "react-router-dom";

import {
  useAuth
} from "../auth/AuthContext";

import {
  ApiError
} from "../lib/api";

export function RegisterPage() {
  const {
    authenticated,
    register
  } = useAuth();

  const navigate = useNavigate();

  const [
    email,
    setEmail
  ] = useState("");

  const [
    password,
    setPassword
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword
  ] = useState("");

  const [
    submitting,
    setSubmitting
  ] = useState(false);

  const [
    error,
    setError
  ] = useState<string | null>(
    null
  );

  if (authenticated) {
    return (
      <Navigate
        to="/app"
        replace
      />
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError(
      null
    );

    if (
      password
      !== confirmPassword
    ) {
      setError(
        "Passwords do not match."
      );

      return;
    }

    setSubmitting(
      true
    );

    try {
      await register(
        email,
        password
      );

      navigate(
        "/app",
        {
          replace: true
        }
      );

    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(
          caughtError.message
        );

      } else {
        setError(
          "Unable to register. Check that the API server is running."
        );
      }

    } finally {
      setSubmitting(
        false
      );
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card">
        <div className="auth-heading">
          <div className="brand-mark">
            AF
          </div>

          <div>
            <p className="eyebrow">
              AI-Fitness
            </p>

            <h1>
              Create account
            </h1>
          </div>
        </div>

        <p className="muted">
          Your account keeps training
          and movement-analysis history
          owner-scoped.
        </p>

        <form
          className="form-stack"
          onSubmit={handleSubmit}
        >
          <label className="field">
            <span>
              Email
            </span>

            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={
                (event) => setEmail(
                  event.target.value
                )
              }
            />
          </label>

          <label className="field">
            <span>
              Password
            </span>

            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              value={password}
              onChange={
                (event) => setPassword(
                  event.target.value
                )
              }
            />
          </label>

          <label className="field">
            <span>
              Confirm password
            </span>

            <input
              type="password"
              autoComplete="new-password"
              required
              minLength={12}
              value={confirmPassword}
              onChange={
                (event) => setConfirmPassword(
                  event.target.value
                )
              }
            />
          </label>

          {error && (
            <div
              className="error-box"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={submitting}
          >
            {
              submitting
              ? "Creating account..."
              : "Create account"
            }
          </button>
        </form>

        <p className="auth-switch">
          Already registered?{" "}

          <Link to="/login">
            Sign in
          </Link>
        </p>
      </section>
    </div>
  );
}