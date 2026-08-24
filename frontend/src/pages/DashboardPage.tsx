import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  Layers,
  Plus,
  Flame,
  CheckCircle2,
  CalendarClock,
  TrendingUp,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CreateDeckDialog } from "@/components/deck/create-deck-dialog";
import { decksApi, type Deck } from "@/api/decks";
import { cardsApi } from "@/api/cards";

/**
 * DashboardPage — Design System MemorAI §§2, 6, 8, 10, 11
 * - Streak usa Flame com text-warning (§11 — nunca primary)
 * - Deck cards: hover border-primary/30 + -translate-y-0.5 (§6.2)
 * - Metric cards: grid-cols-2 sm:grid-cols-4 (§8)
 * - Empty state: padrão definido em §10
 */

export default function DashboardPage() {
  const navigate = useNavigate();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dueCount, setDueCount] = useState<number>(0);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [data, due] = await Promise.all([
          decksApi.list(),
          cardsApi.due().catch(() => [] as never[]),
        ]);
        setDecks(data);
        setDueCount((due as unknown[]).length);
      } catch (err) {
        console.error("Erro ao buscar os decks:", err);
        setError("Não foi possível carregar seus decks.");
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  function handleCreated(deck: Deck) {
    setDecks((prev) => [deck, ...prev]);
  }

  const totalCards = useMemo(
    () => decks.reduce((sum, d) => sum + (d.cards?.length ?? 0), 0),
    [decks]
  );
  const reviewedToday = 12;
  const streak = 7;

  const today = useMemo(
    () =>
      new Date().toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "numeric",
        month: "long",
      }),
    []
  );

  return (
    <AppShell>
      {/* ============ Header da página (§2) ============ */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium capitalize text-muted-foreground">
            {today}
          </p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Bem-vindo de volta
          </h1>
          <p className="text-sm text-muted-foreground">
            {dueCount > 0
              ? `Você tem ${dueCount} ${dueCount === 1 ? "card" : "cards"} para revisar hoje.`
              : "Tudo em dia. Continue praticando!"}
          </p>
        </div>
        <CreateDeckDialog onCreated={handleCreated} />
      </div>

      {/* ============ Métricas (§8 grid) ============ */}
      <div className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:gap-4">
        <MetricCard
          icon={<Flame className="size-4 stroke-2 text-warning" />}
          label="Sequência"
          value={`${streak} dias`}
        />
        <MetricCard
          icon={<CheckCircle2 className="size-4 stroke-2" />}
          label="Revisados hoje"
          value={String(reviewedToday)}
        />
        <MetricCard
          icon={<CalendarClock className="size-4 stroke-2" />}
          label="Para revisar"
          value={String(dueCount)}
          highlight={dueCount > 0}
        />
        <MetricCard
          icon={<TrendingUp className="size-4 stroke-2" />}
          label="Total de cards"
          value={String(totalCards)}
        />
      </div>

      {/* ============ Revisar hoje (destaque) ============ */}
      {dueCount > 0 ? (
        <section className="mb-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Revisar hoje
            </h2>
            <Button variant="ghost" size="sm" onClick={() => navigate("/review")}>
              Ver todos
            </Button>
          </div>
          <Card className="border-primary/30 bg-accent/40">
            <CardContent className="flex items-center justify-between gap-4 p-5">
              <div className="flex items-center gap-4">
                <div className="flex size-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Flame className="size-5 stroke-2" />
                </div>
                <div>
                  <p className="font-semibold">
                    {dueCount} cards esperando você
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Mantenha a sequência revisando agora
                  </p>
                </div>
              </div>
              <Button size="sm" onClick={() => navigate("/review")}>
                Iniciar revisão
              </Button>
            </CardContent>
          </Card>
        </section>
      ) : null}

      {/* ============ Meus decks ============ */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            Meus decks
          </h2>
        </div>

        {loading ? (
          <div
            role="status"
            aria-live="polite"
            className="flex min-h-[200px] items-center justify-center rounded-xl border border-dashed text-muted-foreground"
          >
            Carregando decks...
          </div>
        ) : error ? (
          <Card className="border-destructive/50">
            <CardContent className="pt-6 text-destructive">{error}</CardContent>
          </Card>
        ) : decks.length === 0 ? (
          <EmptyState onCreated={handleCreated} />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {decks.map((deck) => (
              <DeckCard key={deck.id} deck={deck} />
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}

function MetricCard({
  icon,
  label,
  value,
  highlight,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? "border-primary/40" : ""}>
      <CardContent className="p-4">
        <div className="mb-2 flex items-center gap-2 text-muted-foreground">
          {icon}
          <span className="text-xs font-medium">{label}</span>
        </div>
        <p className="text-xl font-semibold">{value}</p>
      </CardContent>
    </Card>
  );
}

function DeckCard({ deck }: { deck: Deck }) {
  const total = deck.cards?.length ?? 0;
  const due = 0; // TODO: trocar por /cards/due/ quando o endpoint existir
  const progress = total > 0 ? 100 : 0; // TODO: derivar de reviews feitas

  return (
    <Card className="group relative transition-all hover:border-primary/30 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="mb-2 flex items-start justify-between">
          <div className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Layers className="size-5 stroke-2" />
          </div>
          {due > 0 ? (
            <Badge variant="default">{due} p/ hoje</Badge>
          ) : (
            <Badge variant="success">em dia</Badge>
          )}
        </div>
        <CardTitle className="text-base">{deck.name}</CardTitle>
        {deck.description ? (
          <CardDescription className="line-clamp-2">
            {deck.description}
          </CardDescription>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        <div>
          <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
            <span>{total} cards</span>
          </div>
          <Progress value={progress} />
        </div>

        <Button
          variant={due > 0 ? "default" : "outline"}
          size="sm"
          className="w-full"
        >
          {due > 0 ? "Revisar agora" : "Praticar"}
        </Button>
      </CardContent>
    </Card>
  );
}

function EmptyState({ onCreated }: { onCreated: (deck: Deck) => void }) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Layers className="size-6 stroke-2" />
        </div>
        <div className="space-y-1">
          <p className="font-medium">Nenhum deck encontrado</p>
          <p className="text-sm text-muted-foreground">
            Crie seu primeiro deck para começar a praticar repetição espaçada.
          </p>
        </div>
        <CreateDeckDialog onCreated={onCreated} trigger={
          <Button>
            <Plus className="size-4 stroke-2" />
            Criar primeiro deck
          </Button>
        } />
      </CardContent>
    </Card>
  );
}
