import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { aiApi } from "@/api/ai";
import { cardsApi } from "@/api/cards";
import { GenerateCardsDialog } from "@/components/deck/generate-cards-dialog";

jest.mock("@/api/ai", () => ({ aiApi: { generateCards: jest.fn() } }));
jest.mock("@/api/cards", () => ({ cardsApi: { create: jest.fn() } }));

const ai = aiApi as jest.Mocked<typeof aiApi>;
const cards = cardsApi as jest.Mocked<typeof cardsApi>;

beforeEach(() => jest.resetAllMocks());

async function openAndGenerate() {
  await userEvent.click(screen.getByRole("button", { name: /Gerar com IA/ }));
  await userEvent.type(screen.getByLabelText("Tópico"), "decorators");
  await userEvent.click(screen.getByRole("button", { name: "Gerar" }));
}

test("gera, desmarca um card e salva só os escolhidos", async () => {
  ai.generateCards.mockResolvedValue({
    status: "success",
    model: "m",
    provider: "p",
    prompt_version: "1.0",
    cards: [
      { front: "Q1?", back: "A1" },
      { front: "Q2?", back: "A2" },
    ],
  });
  cards.create.mockImplementation(async (input) => ({ id: 1, ...input }) as never);
  const onCreated = jest.fn();

  render(<GenerateCardsDialog deckId={9} onCreated={onCreated} />);
  await openAndGenerate();

  await userEvent.click(await screen.findByLabelText(/Q2\?/));
  await userEvent.click(screen.getByRole("button", { name: "Salvar 1 card" }));

  await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
  expect(cards.create).toHaveBeenCalledTimes(1);
  expect(cards.create).toHaveBeenCalledWith({ deck: 9, front: "Q1?", back: "A1" });
});

test("sem cards na resposta mostra erro e permite tentar de novo", async () => {
  ai.generateCards.mockResolvedValue({
    status: "fallback",
    model: "",
    provider: "",
    prompt_version: "1.0",
    cards: [],
  });
  render(<GenerateCardsDialog deckId={1} onCreated={jest.fn()} />);
  await openAndGenerate();
  expect(await screen.findByRole("alert")).toHaveTextContent("não conseguiu gerar");
  expect(screen.getByRole("button", { name: "Gerar" })).toBeEnabled();
});
