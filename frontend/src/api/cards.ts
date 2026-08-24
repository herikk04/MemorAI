import api from "./api";

/**
 * Cards API — MemorAI (backend: flashcards/views).
 *
 * Endpoints:
 *   GET    /cards/                      lista cards do user
 *   GET    /cards/due/                  cards cujo now >= due
 *   GET    /decks/{id}/cards/           (via /decks/{id}/) — não exposto; use GET /cards/?deck=
 *   POST   /cards/                      cria card
 *   PATCH  /cards/{id}/                 edita card (front, back, srs_algorithm)
 *   DELETE /cards/{id}/                 remove
 *   POST   /cards/{id}/review/          registra review + IA feedback best-effort
 *
 * Card serializer fields (flashcards/serializers.CardSerializer):
 *   id, deck, front, back, interval, ease, reps, lapses, due, last_reviewed_at, srs_algorithm
 */

export type SRSAlgorithm = "fsrs" | "sm2" | "anki";

/** RatingAgain=1 Hard=2 Good=3 Easy=4 (flashcards/models.Review.Rating). */
export type ReviewRating = 1 | 2 | 3 | 4;

export interface Card {
  id: number;
  deck: number;
  front: string;
  back: string;
  interval: number;
  ease: number;
  reps: number;
  lapses: number;
  due: string | null;
  last_reviewed_at: string | null;
  srs_algorithm: SRSAlgorithm;
}

export interface CardCreateInput {
  deck: number;
  front: string;
  back: string;
  srs_algorithm?: SRSAlgorithm;
}

export interface CardUpdateInput {
  front?: string;
  back?: string;
  srs_algorithm?: SRSAlgorithm;
}

export interface Review {
  id: number;
  card: number;
  rating: ReviewRating;
  reviewed_at: string;
  time_ms: number;
  feedback_text: string;
  feedback_source: string;
}

/** POST /cards/{id}/review/ -> response body. */
export interface ReviewResponse {
  card: Card;
  review: Review;
}

export const cardsApi = {
  async list(deckId?: number): Promise<Card[]> {
    const params = deckId ? { deck: deckId } : undefined;
    const { data } = await api.get<Card[]>("/cards/", { params });
    return data;
  },
  async due(): Promise<Card[]> {
    const { data } = await api.get<Card[]>("/cards/due/");
    return data;
  },
  async create(input: CardCreateInput): Promise<Card> {
    const { data } = await api.post<Card>("/cards/", input);
    return data;
  },
  async update(id: number, input: CardUpdateInput): Promise<Card> {
    const { data } = await api.patch<Card>(`/cards/${id}/`, input);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/cards/${id}/`);
  },
  async review(id: number, rating: ReviewRating, time_ms = 0): Promise<ReviewResponse> {
    const { data } = await api.post<ReviewResponse>(
      `/cards/${id}/review/`,
      { rating, time_ms }
    );
    return data;
  },
};
