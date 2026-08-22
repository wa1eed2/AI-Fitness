import {
  FormEvent,
  useState
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate
} from "react-router-dom";

import {
  useAuth
} from "../auth/AuthContext";

import {
  ApiError
} from "../lib/api";


interface LocationState {
  from?: string;
}


export function LoginPage() {
  const {
    authenticated,
    login
  } = useAuth();

  const navigate = useNavigate();

  const location = useLocation();

  const [
    email,
    setEmail
  ] = useState("");

  const [
    password,
    setPassword
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

    setSubmitting(
      true
    );

    try {
      await login(
        email,
        password
      );

      const state = location.state as LocationState | null;

      navigate(
        state?.from ?? "/app",
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
          "Unable to sign in. Check that the API server is running."
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
              Welcome back
            </h1>
          </div>
        </div>

        <p className="muted">
          Sign in to view training,
          progress, and movement analysis.
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
              autoComplete="current-password"
              required
              value={password}
              onChange={
                (event) => setPassword(
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
              ? "Signing in..."
              : "Sign in"
            }
          </button>
        </form>

        <p className="auth-switch">
          New to AI-Fitness?{" "}

          <Link to="/register">
            Create an account
          </Link>
        </p>
      </section>
    </div>
  );
}