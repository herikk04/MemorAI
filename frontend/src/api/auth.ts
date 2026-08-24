import api from "./api";
import { tokenService, type LoginResponse } from "@/lib/token-service";

/**
 * Auth API — MemorAI (backend: apps/users/views).
 *
 * POST /auth/login/  -> { access, refresh, user_id, username, language }
 * POST /auth/refresh/-> { access, refresh } (rotaciona e blacklist o antigo)
 * POST /auth/verify/ -> 200 se access válido
 */
export const authApi = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login/", {
      username,
      password,
    });
    tokenService.setSession(data);
    return data;
  },
  async logout(): Promise<void> {
    tokenService.clear();
  },
  async verify(): Promise<boolean> {
    const access = tokenService.getAccess();
    if (!access) return false;
    try {
      await api.post("/auth/verify/", { token: access });
      return true;
    } catch {
      return false;
    }
  },
};
