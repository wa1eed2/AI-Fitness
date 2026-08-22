import {
  createContext,
  ReactNode,
  useContext,
  useMemo,
  useState
} from "react";

import {
  ApiError,
  loginAccount,
  logoutAccount,
  registerAccount
} from "../lib/api";

const SESSION_STORAGE_KEY = (
  "ai-fitness-auth-session"
);

export interface AuthSession {
  userId: number;
  email: string;
  accessToken: string;
}

interface AuthContextValue {
  session: AuthSession | null;
  authenticated: boolean;
  login: (
    email: string,
    password: string
  ) => Promise<void>;
  register: (
    email: string,
    password: string
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<
  AuthContextValue | undefined
>(
  undefined
);

function readStoredSession():
  AuthSession | null {
  try {
    const stored = sessionStorage.getItem(
      SESSION_STORAGE_KEY
    );

    if (!stored) {
      return null;
    }

    const parsed = JSON.parse(
      stored
    ) as Partial<AuthSession>;

    if (
      typeof parsed.userId !== "number"
      || typeof parsed.email !== "string"
      || typeof parsed.accessToken !== "string"
      || !parsed.accessToken
    ) {
      sessionStorage.removeItem(
        SESSION_STORAGE_KEY
      );

      return null;
    }

    return {
      userId: parsed.userId,
      email: parsed.email,
      accessToken: parsed.accessToken
    };

  } catch {
    sessionStorage.removeItem(
      SESSION_STORAGE_KEY
    );

    return null;
  }
}

function storeSession(
  session: AuthSession | null
): void {
  if (session === null) {
    sessionStorage.removeItem(
      SESSION_STORAGE_KEY
    );

    return;
  }

  sessionStorage.setItem(
    SESSION_STORAGE_KEY,
    JSON.stringify(
      session
    )
  );
}

export function AuthProvider({
  children
}: {
  children: ReactNode;
}) {
  const [
    session,
    setSession
  ] = useState<AuthSession | null>(
    () => readStoredSession()
  );

  async function login(
    email: string,
    password: string
  ): Promise<void> {
    const normalizedEmail = (
      email.trim().toLowerCase()
    );

    const response = await loginAccount(
      normalizedEmail,
      password
    );

    const newSession: AuthSession = {
      userId: response.user_id,
      email: response.email ?? normalizedEmail,
      accessToken: response.access_token
    };

    storeSession(
      newSession
    );

    setSession(
      newSession
    );
  }

  async function register(
    email: string,
    password: string
  ): Promise<void> {
    const normalizedEmail = (
      email.trim().toLowerCase()
    );

    const response = await registerAccount(
      normalizedEmail,
      password
    );

    const newSession: AuthSession = {
      userId: response.user_id,
      email: response.email ?? normalizedEmail,
      accessToken: response.access_token
    };

    storeSession(
      newSession
    );

    setSession(
      newSession
    );
  }

  async function logout():
    Promise<void> {
    const accessToken = (
      session?.accessToken
      ?? null
    );

    try {
      if (accessToken) {
        await logoutAccount(
          accessToken
        );
      }

    } catch (error) {
      if (
        !(
          error instanceof ApiError
          && (
            error.status === 401
            || error.status === 403
          )
        )
      ) {
        console.error(
          "Backend logout failed",
          error
        );
      }

    } finally {
      storeSession(
        null
      );

      setSession(
        null
      );
    }
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      authenticated: (
        session !== null
      ),
      login,
      register,
      logout
    }),
    [
      session
    ]
  );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth():
  AuthContextValue {
  const context = useContext(
    AuthContext
  );

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}