import { tokenService } from "@/lib/token-service";

const session = {
  access: "a1",
  refresh: "r1",
  user_id: 7,
  username: "ana",
  language: "pt" as const,
};

beforeEach(() => sessionStorage.clear());

test("setSession guarda tokens e usuário", () => {
  tokenService.setSession(session);
  expect(tokenService.isAuthenticated()).toBe(true);
  expect(tokenService.getAccess()).toBe("a1");
  expect(tokenService.getRefresh()).toBe("r1");
  expect(tokenService.getUser()).toEqual({ id: 7, username: "ana", language: "pt" });
});

test("setTokens troca o refresh rotacionado e mantém o usuário", () => {
  tokenService.setSession(session);
  tokenService.setTokens("a2", "r2");
  expect(tokenService.getAccess()).toBe("a2");
  expect(tokenService.getRefresh()).toBe("r2");
  expect(tokenService.getUser()?.username).toBe("ana");
});

test("setTokens sem refresh preserva o atual", () => {
  tokenService.setSession(session);
  tokenService.setTokens("a2");
  expect(tokenService.getRefresh()).toBe("r1");
});

test("clear encerra a sessão", () => {
  tokenService.setSession(session);
  tokenService.clear();
  expect(tokenService.isAuthenticated()).toBe(false);
  expect(tokenService.getUser()).toBeNull();
});
