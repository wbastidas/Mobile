import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const ROLE_LABEL: Record<string, string> = {
  ADMIN: "Administrador",
  OPERATOR_MATRIZ: "Operador Matriz",
  OPERATOR_UN: "Operador UN",
  VIEWER_MATRIZ: "Visualizador Matriz",
  VIEWER_UN: "Visualizador UN",
  FIELD: "Campo",
};

export default function Layout() {
  const { user, logout, isOperator, isAdmin } = useAuth();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          Levantamiento<br />
          <span>Eléctrico</span> · Admin
        </div>
        <nav>
          <NavLink to="/" end className="nav-link">
            Dashboard
          </NavLink>
          <NavLink to="/works" className="nav-link">
            Trabajos
          </NavLink>
          <NavLink to="/devices" className="nav-link">
            Dispositivos
          </NavLink>
          {isAdmin && (
            <NavLink to="/users" className="nav-link">
              Usuarios
            </NavLink>
          )}
          {isOperator && (
            <NavLink to="/quality" className="nav-link">
              Parámetros de calidad
            </NavLink>
          )}
          <NavLink to="/reports" className="nav-link">
            Reportes
          </NavLink>
          <NavLink to="/audit" className="nav-link">
            Auditoría
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <div>{user?.full_name}</div>
          <div className="muted">
            {ROLE_LABEL[user?.role ?? ""] ?? user?.role}
            {user && !user.is_global_scope ? " · UN local" : " · Global"}
          </div>
          <button onClick={logout}>Cerrar sesión</button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
