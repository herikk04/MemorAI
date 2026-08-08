/**
 * Token service — MemorAI
 *
 * JWT access+refresh guardados em sessionStorage (escopo por aba). Storage de
 * autenticacão fica isolada da theme-storage (que é localPersistente). Quando
 * voltar a UI, logar de novo é incentivo certo; em sessionStorage o token não
 * persiste entre sessões do navegador.
 *
 * Login response (backend: apps/users/serializers.LoginTokenSerializer):
 *   { access, refresh, user_id, username, language }
 */

const ACCESS_KEY = "memorai-access";
const REFRESH_KEY = "memorai-refresh";
const USER_KEY = "memorai-user";

export interface AuthUser {
  id: number;
  username: string;
  language: "pt" | "en";
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user_id: number;
  username: string;
  language: "pt" | "en";
}

export const tokenService = {
  getAccess(): string | null {
    return sessionStorage.getItem(ACCESS_KEY);
  },
  getRefresh(): string | null {
    return sessionStorage.getItem(REFRESH_KEY);
  },
  getUser(): AuthUser | null {
    const raw = sessionStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  },
  setSession(data: LoginResponse): void {
    sessionStorage.setItem(ACCESS_KEY, data.access);
    sessionStorage.setItem(REFRESH_KEY, data.refresh);
    sessionStorage.setItem(
      USER_KEY,
      JSON.stringify({
        id: data.user_id,
        username: data.username,
        language: data.language,
      } as AuthUser)
    );
  },
  clear(): void {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(USER_KEY);
  },
  isAuthenticated(): boolean {
    return Boolean(sessionStorage.getItem(ACCESS_KEY));
  },
};
