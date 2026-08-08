import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  Layers,
  Plus,
  Flame,
  CheckCircle2,
  CalendarClock,
  TrendingUp,
} from "lucide-react";

import api from "@/api/api";
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

interface Deck {
  id: number;
  name: string;
  description?: string;
  tags?: string[];
  totalCards?: number;
  dueToday?: number;
  progress?: number;
}

export default function DashboardPage() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDecks = async () => {
      try {
        const response = await api.get<Deck[]>("/decks/");
        setDecks(response.data);
      } catch (err) {
        console.error("Erro ao buscar os decks:", err);
        setError("Não foi possível carregar seus decks.");
      } finally {
        setLoading(false);
      }
    };
    fetchDecks();
  }, []);

  const dueCount = decks.reduce((sum, d) => sum + (d.dueToday ?? 0), 0);
  const totalCards = decks.reduce((sum, d) => sum + (d.totalCards ?? 0), 0);
  const reviewedToday = 12;
  const streak = 7;

  return (
    <AppShell>
      {/* ============ Header ============ */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Sexta-feira, 7 de agosto</p>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Bem-vindo de volta
          </h1>
          <p className="text-muted-foreground">
            {dueCount > 0
              ? `Você tem ${dueCount} ${dueCount === 1 ? "card" : "cards"} para revisar hoje.`
              : "Tudo em dia. Continue praticando!"}
          </p>
        </div>
        <Button>
          <Plus className="size-4" />
          Novo deck
        </Button>
      </div>

      {/* ============ Métricas ============ */}
      <div className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:gap-4">
        <MetricCard
          icon={<Flame className="size-4" />}
          label="Sequência"
          value={`${streak} dias`}
        />
        <MetricCard
          icon={<CheckCircle2 className="size-4" />}
          label="Revisados hoje"
          value={String(reviewedToday)}
        />
        <MetricCard
          icon={<CalendarClock className="size-4" />}
          label="Para revisar"
          value={String(dueCount)}
          highlight={dueCount > 0}
        />
        <MetricCard
          icon={<TrendingUp className="size-4" />}
          label="Total de cards"
          value={String(totalCards)}
        />
      </div>

      {/* ============ Revisar hoje ============ */}
      {dueCount > 0 && (
        <section className="mb-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Revisar hoje
            </h2>
            <Button variant="ghost" size="sm">
              Ver todos
            </Button>
          </div>
          <Card className="border-primary/30 bg-accent/30">
            <CardContent className="flex items-center justify-between gap-4 p-5">
              <div className="flex items-center gap-4">
                <div className="flex size-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Flame className="size-5" />
                </div>
                <div>
                  <p className="font-semibold">{dueCount} cards esperando você</p>
                  <p className="text-sm text-muted-foreground">
                    Mantenha a sequência revisando agora
                  </p>
                </div>
              </div>
              <Button size="sm">Iniciar revisão</Button>
            </CardContent>
          </Card>
        </section>
      )}

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
            className="flex min-h-[200px] items-center justify-center rounded-xl border border-dashed text-muted-foreground"
          >
            Carregando decks...
          </div>
        ) : error ? (
          <Card className="border-destructive/50">
            <CardContent className="pt-6 text-destructive">{error}</CardContent>
          </Card>
        ) : decks.length === 0 ? (
          <EmptyState />
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
  const total = deck.totalCards ?? 0;
  const due = deck.dueToday ?? 0;
  const progress = deck.progress ?? 0;

  return (
    <Card className="group relative transition-all hover:border-primary/40 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="mb-2 flex items-start justify-between">
          <div className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Layers className="size-5" />
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
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {deck.tags?.length ? (
          <div className="flex flex-wrap gap-1">
            {deck.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px]">
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}

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

function EmptyState() {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Layers className="size-6" />
        </div>
        <div className="space-y-1">
          <p className="font-medium">Nenhum deck encontrado</p>
          <p className="text-sm text-muted-foreground">
            Crie seu primeiro deck para começar a praticar repetição espaçada.
          </p>
        </div>
        <Button>
          <Plus className="size-4" />
          Criar primeiro deck
        </Button>
      </CardContent>
    </Card>
  );
}
