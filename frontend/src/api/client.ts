import axios from "axios";

const TOKEN_KEY = "le_access_token";
const REFRESH_KEY = "le_refresh_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const api = axios.create({ baseURL: "/api/v1" });

// Inyecta el token JWT en cada petición.
api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intento único de refresh ante 401; si falla, limpia la sesión.
let refreshing: Promise<string | null> | null = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    if (status === 401 && !original._retry && tokenStore.getRefresh()) {
      original._retry = true;
      try {
        refreshing =
          refreshing ??
          axios
            .post("/api/v1/auth/refresh", { refresh_token: tokenStore.getRefresh() })
            .then((r) => {
              tokenStore.set(r.data.access_token, r.data.refresh_token);
              return r.data.access_token as string;
            })
            .catch(() => null)
            .finally(() => {
              refreshing = null;
            });
        const newToken = await refreshing;
        if (newToken) {
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        }
      } catch {
        /* cae al clear de abajo */
      }
      tokenStore.clear();
    }
    return Promise.reject(error);
  }
);

// Extrae un mensaje de error legible desde una respuesta de FastAPI.
export function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
    return err.message;
  }
  return "Error inesperado.";
}
