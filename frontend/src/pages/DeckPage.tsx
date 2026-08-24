import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Layers,
  Plus,
  Loader2,
  Pencil,
  Trash2,
  Flame,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card as CardUI,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { decksApi, type Deck } from "@/api/decks";
import { cardsApi, type Card } from "@/api/cards";

/**
 * DeckPage — detalhe de um deck (/decks/:deckId).
 *
 * Lista cards do deck, cria novo card (POST /cards/) e permite revisar
 * cards devidos desse deck (link para /review, que usa /cards/due/ global;
 * uma melhoria futura seria filtrar a sessão por deck).
 */
type DeckPageParams = { deckId: string };

export default function DeckPage() {
  const { deckId } = useParams<DeckPageParams>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    if (!deckId) return;
    try {
      setLoading(true);
      // Deck list é scoped por owner; encontrar o deck nela é suficiente.
      const decks = await decksApi.list();
      const found = decks.find((d) => d.id === Number(deckId));
      if (!found) {
        setError("Deck não encontrado.");
        return;
      }
      setDeck(found);
      const cards = await cardsApi.list(found.id);
      setCards(cards);
    } catch (err) {
      console.error("Erro ao carregar deck:", err);
      setError("Não foi possível carregar o deck.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deckId]);

  function handleCardCreated(card: Card) {
    setCards((prev) => [card, ...prev]);
  }
  function handleCardRemoved(cardId: number) {
    setCards((prev) => prev.filter((c) => c.id !== cardId));
  }

  if (loading) {
    return (
      <AppShell>
        <div className="flex min-h-[400px] items-center justify-center text-muted-foreground">
          <Loader2 className="size-6 stroke-2 animate-spin" />
        </div>
      </AppShell>
    );
  }

  if (error || !deck) {
    return (
      <AppShell>
        <Button
          variant="ghost"
          size="sm"
          className="mb-4"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft className="size-4 stroke-2" /> Voltar
        </Button>
        <CardUI className="border-destructive/50">
          <CardContent className="pt-6 text-destructive">
            {error ?? "Deck inválido."}
          </CardContent>
        </CardUI>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-6 flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/dashboard")}
          aria-label="Voltar ao dashboard"
        >
          <ArrowLeft className="size-4 stroke-2" />
        </Button>
      </div>

      {/* Header do deck */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <Layers className="size-5 stroke-2" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              {deck.name}
            </h1>
          </div>
          {deck.description ? (
            <p className="text-sm text-muted-foreground">{deck.description}</p>
          ) : null}
          <p className="text-xs text-muted-foreground">
            {cards.length} {cards.length === 1 ? "card" : "cards"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => navigate("/review")}>
            <Flame className="size-4 stroke-2" />
            Revisar
          </Button>
          <CreateCardDialog deckId={deck.id} onCreated={handleCardCreated} />
        </div>
      </div>

      {/* Lista de cards */}
      {cards.length === 0 ? (
        <CardUI className="border-dashed">
          <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <Plus className="size-6 stroke-2" />
            </div>
            <div className="space-y-1">
              <p className="font-medium">Nenhum card neste deck</p>
              <p className="text-sm text-muted-foreground">
                Crie seu primeiro card para começar a praticar.
              </p>
            </div>
            <CreateCardDialog
              deckId={deck.id}
              onCreated={handleCardCreated}
              trigger={
                <Button>
                  <Plus className="size-4 stroke-2" />
                  Criar primeiro card
                </Button>
              }
            />
          </CardContent>
        </CardUI>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onRemoved={handleCardRemoved}
            />
          ))}
        </div>
      )}
    </AppShell>
  );
}

function CardItem({
  card,
  onRemoved,
}: {
  card: Card;
  onRemoved: (id: number) => void;
}) {
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await cardsApi.remove(card.id);
      onRemoved(card.id);
    } catch (err) {
      console.error("Erro ao deletar card:", err);
      setDeleting(false);
    }
  }

  return (
    <CardUI className="transition-all hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-1 text-sm font-medium">
            {card.front}
          </CardTitle>
          <Badge variant={card.reps > 0 ? "success" : "outline"}>
            {card.reps} reps
          </Badge>
        </div>
        <CardDescription className="line-clamp-3">
          {card.back}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex justify-end gap-1 pt-0">
        <Button variant="ghost" size="icon" aria-label="Editar card" disabled>
          <Pencil className="size-4 stroke-2" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDelete}
          disabled={deleting}
          aria-label="Excluir card"
        >
          {deleting ? (
            <Loader2 className="size-4 stroke-2 animate-spin" />
          ) : (
            <Trash2 className="size-4 stroke-2" />
          )}
        </Button>
      </CardContent>
    </CardUI>
  );
}

function CreateCardDialog({
  deckId,
  onCreated,
  trigger,
}: {
  deckId: number;
  onCreated: (card: Card) => void;
  trigger?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const card = await cardsApi.create({
        deck: deckId,
        front: front.trim(),
        back: back.trim(),
      });
      onCreated(card);
      setFront("");
      setBack("");
      setOpen(false);
    } catch (err) {
      console.error("Falha ao criar card:", err);
      setError("Não foi possível criar o card.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <Plus className="size-4 stroke-2" />
            Novo card
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <DialogHeader>
            <DialogTitle>Novo card</DialogTitle>
            <DialogDescription>
              Pergunta (front) e resposta (back) usadas na repetição espaçada.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="card-front">Pergunta (frente)</Label>
              <Textarea
                id="card-front"
                placeholder="Ex.: O que faz o decorator @staticmethod?"
                value={front}
                onChange={(e) => setFront(e.target.value)}
                rows={3}
                autoFocus
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="card-back">Resposta (verso)</Label>
              <Textarea
                id="card-back"
                placeholder="Ex.: Transforma um método em um método que..."
                value={back}
                onChange={(e) => setBack(e.target.value)}
                rows={4}
                required
              />
            </div>
          </div>

          {error ? (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          ) : null}

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={submitting}>
                Cancelar
              </Button>
            </DialogClose>
            <Button type="submit" disabled={submitting || !front.trim() || !back.trim()}>
              {submitting ? (
                <>
                  <Loader2 className="size-4 stroke-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Plus className="size-4 stroke-2" />
                  Criar card
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
