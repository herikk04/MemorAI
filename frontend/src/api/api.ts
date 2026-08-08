import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { tokenService } from "@/lib/token-service";

/**
 * Axios instance com interceptors de auth (SDD 5.4 — Frontend -> Backend).
 *
 * - Request: injeta Authorization: Bearer <access> quando existe token.
 * - Response 401: tenta refresh uma vez (evita loop); se falhar, limpa sessão
 *   e sinaliza para o router redirecionar para /login.
 */

const baseURL =
  process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL, timeout: 30_000 });

let onUnauthorized: (() => void) | null = null;
export function registerUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const access = tokenService.getAccess();
  if (access) {
    config.headers.set("Authorization", `Bearer ${access}`);
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  const refresh = tokenService.getRefresh();
  if (!refresh) return null;
  try {
    const response = await axios.post(
      `${baseURL}/auth/refresh/`,
      { refresh },
      { timeout: 15_000 }
    );
    const next = response.data?.access as string | undefined;
    if (next) {
      sessionStorage.setItem("memorai-access", next);
      return next;
    }
    return null;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    // Não tenta refresh para endpoints de auth (login/refresh/verify).
    const isAuthEndpoint = original?.url?.includes("/auth/");
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !isAuthEndpoint
    ) {
      original._retry = true;
      if (!refreshing) refreshing = tryRefresh().finally(() => (refreshing = null));
      const next = await refreshing;
      if (next) {
        original.headers.set("Authorization", `Bearer ${next}`);
        return api(original);
      }
      tokenService.clear();
      onUnauthorized?.();
    }
    return Promise.reject(error);
  }
);

export default api;
