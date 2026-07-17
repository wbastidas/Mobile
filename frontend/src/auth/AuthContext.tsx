import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, tokenStore } from "@/api/client";
import { authApi } from "@/api/endpoints";
import type { CurrentUser, Role } from "@/types";

interface AuthState {
  user: CurrentUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
  isOperator: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

const OPERATOR_ROLES: Role[] = ["ADMIN", "OPERATOR_MATRIZ", "OPERATOR_UN"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const data = await authApi.login(username, password);
    tokenStore.set(data.access_token, data.refresh_token);
    api.defaults.headers.common.Authorization = `Bearer ${data.access_token}`;
    setUser(await authApi.me());
  };

  const logout = () => {
    tokenStore.clear();
    setUser(null);
  };

  const hasRole = (...roles: Role[]) => !!user && roles.includes(user.role);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        hasRole,
        isOperator: !!user && OPERATOR_ROLES.includes(user.role),
        isAdmin: user?.role === "ADMIN",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
