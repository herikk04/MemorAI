import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { aiApi } from "@/api/ai";
import { SearchDialog } from "@/components/layout/search-dialog";

jest.mock("@/api/ai", () => ({ aiApi: { search: jest.fn() } }));
const ai = aiApi as jest.Mocked<typeof aiApi>;

function renderDialog(onOpenChange = jest.fn()) {
  render(
    <MemoryRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/" element={<SearchDialog open onOpenChange={onOpenChange} />} />
        <Route path="/decks/:id" element={<p>página do deck</p>} />
      </Routes>
    </MemoryRouter>
  );
  return onOpenChange;
}

beforeEach(() => jest.resetAllMocks());

test("busca no Enter e abre o deck do resultado", async () => {
  ai.search.mockResolvedValue({
    query: "loop",
    status: "success",
    hits: [
      { card_id: 1, front: "Como usar enumerate?", back: "for i, x in enumerate(l)", deck_id: 4, deck_name: "Python", score: 0.9 },
    ],
  });
  const onOpenChange = renderDialog();
  await userEvent.type(screen.getByLabelText("Buscar"), "loop com índice{enter}");

  expect(ai.search).toHaveBeenCalledWith("loop com índice");
  await userEvent.click(await screen.findByText("Como usar enumerate?"));
  expect(onOpenChange).toHaveBeenCalledWith(false);
  expect(await screen.findByText("página do deck")).toBeInTheDocument();
});

test("sem resultados mostra aviso", async () => {
  ai.search.mockResolvedValue({ query: "x", status: "success", hits: [] });
  renderDialog();
  await userEvent.type(screen.getByLabelText("Buscar"), "x{enter}");
  expect(await screen.findByText("Nenhum card encontrado.")).toBeInTheDocument();
});

test("erro de rede mostra mensagem", async () => {
  ai.search.mockRejectedValue(new Error("boom"));
  renderDialog();
  await userEvent.type(screen.getByLabelText("Buscar"), "x{enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível buscar");
});
