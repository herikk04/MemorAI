import api from "./api";

export interface DeckStats {
  id: number;
  name: string;
  total_cards: number;
  due_count: number;
  learned_cards: number;
}

export interface DashboardStats {
  due_count: number;
  total_cards: number;
  reviewed_today: number;
  streak_days: number;
  /** Fração 0..1 de revisões != Again nos últimos 30 dias; null sem histórico. */
  retention_30d: number | null;
  decks: DeckStats[];
}

export const dashboardApi = {
  async get(): Promise<DashboardStats> {
    const { data } = await api.get<DashboardStats>("/dashboard/");
    return data;
  },
};
