import api from "./api";

export interface Deck {
  id: number;
  name: string;
  description?: string | null;
  owner: number | null;
  cards?: Array<{ id: number }>;
}

export interface DeckCreateInput {
  name: string;
  description?: string;
}

export const decksApi = {
  async list(): Promise<Deck[]> {
    const { data } = await api.get<Deck[]>("/decks/");
    return data;
  },
  async create(input: DeckCreateInput): Promise<Deck> {
    const { data } = await api.post<Deck>("/decks/", input);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/decks/${id}/`);
  },
};
