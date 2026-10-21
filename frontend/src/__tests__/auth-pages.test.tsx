import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { authApi } from "@/api/auth";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";

jest.mock("@/api/auth", () => ({
  authApi: { login: jest.fn(), register: jest.fn() },
}));

const mocked = authApi as jest.Mocked<typeof authApi>;

function renderAt(path: string) {
  return render(
    <MemoryRouter
      initialEntries={[path]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<p>dashboard</p>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  sessionStorage.clear();
  jest.resetAllMocks();
});

test("login com sucesso leva ao dashboard", async () => {
  mocked.login.mockResolvedValue({} as never);
  renderAt("/login");
  await userEvent.type(screen.getByLabelText("Usuário"), "ana");
  await userEvent.type(screen.getByLabelText("Senha"), "s3nha-forte");
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
  expect(mocked.login).toHaveBeenCalledWith("ana", "s3nha-forte");
  expect(await screen.findByText("dashboard")).toBeInTheDocument();
});

test("login inválido mostra erro", async () => {
  mocked.login.mockRejectedValue(new Error("401"));
  renderAt("/login");
  await userEvent.type(screen.getByLabelText("Usuário"), "ana");
  await userEvent.type(screen.getByLabelText("Senha"), "errada");
  await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("inválidos");
});

test("cadastro envia os dados e entra no dashboard", async () => {
  mocked.register.mockResolvedValue({} as never);
  renderAt("/register");
  await userEvent.type(screen.getByLabelText("Usuário"), "bia");
  await userEvent.type(screen.getByLabelText("Senha"), "s3nha-forte-123");
  await userEvent.click(screen.getByRole("button", { name: "Criar conta" }));
  await waitFor(() =>
    expect(mocked.register).toHaveBeenCalledWith({
      username: "bia",
      password: "s3nha-forte-123",
      email: "",
    })
  );
  expect(await screen.findByText("dashboard")).toBeInTheDocument();
});

test("login tem link para o cadastro", async () => {
  renderAt("/login");
  await userEvent.click(screen.getByRole("link", { name: "Criar conta" }));
  expect(await screen.findByText(/Crie sua conta/)).toBeInTheDocument();
});
