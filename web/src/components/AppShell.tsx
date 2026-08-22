import {
  NavLink,
  Outlet,
  useNavigate
} from "react-router-dom";

import {
  useAuth
} from "../auth/AuthContext";

export function AppShell() {
  const {
    session,
    logout
  } = useAuth();

  const navigate = useNavigate();

  async function handleLogout() {
    await logout();

    navigate(
      "/login",
      {
        replace: true
      }
    );
  }

  function navClassName({
    isActive
  }: {
    isActive: boolean;
  }) {
    return (
      isActive
      ? "nav-link nav-link-active"
      : "nav-link"
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            AF
          </div>

          <div>
            <strong>
              AI-Fitness
            </strong>

            <span>
              Training intelligence
            </span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/app"
            end
            className={navClassName}
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/app/vision"
            className={navClassName}
          >
            Movement analysis
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <div className="signed-in-user">
            <span>
              Signed in
            </span>

            <strong>
              {session?.email}
            </strong>
          </div>

          <button
            type="button"
            className="secondary-button full-width"
            onClick={handleLogout}
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}