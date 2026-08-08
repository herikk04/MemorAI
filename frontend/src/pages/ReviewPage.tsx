import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Loader2,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { cardsApi, type Card as CardData, type ReviewRating } from "@/api/cards";
import { cn } from "@/lib/utils";

/**
 * ReviewPage — sessão de repetição espaçada.
 *
 * Flow:
 *  1. GET /cards/due/ carrega fila de cards vencidos
 *  2. Mostra front; card "vira" ao clicar (revela back)
 *  3. Again/Hard/Good/Easy (cores §11) -> POST /cards/{id}/review/
 *  4. Mostra feedback IA (result.review.feedback_text) por ~2s
 *  5. Avança pra proxima pergunta; fim -> tela de sessão concluida
 */

type Phase = "front" | "back" | "feedback" | "finished";

const RATING_BUTTONS: {
  rating: ReviewRating;
  label: string;
  shortcut: string;
  className: string;
}[] = [
  {
    rating: 1,
    label: "Again",
    shortcut: "1",
    className: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  },
  {
    rating: 2,
    label: "Hard",
    shortcut: "2",
    className: "bg-warning text-warning-foreground hover:bg-warning/90",
  },
  {
    rating: 3,
    label: "Good",
    shortcut: "3",
    className: "bg-primary text-primary-foreground hover:bg-primary/90",
  },
  {
    rating: 4,
    label: "Easy",
    shortcut: "4",
    className: "bg-success text-success-foreground hover:bg-success/90",
  },
];

export default function ReviewPage() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<CardData[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>("front");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFeedback, setLastFeedback] = useState<string | null>(null);
  const [feedbackSource, setFeedbackSource] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [showedCount, setShowedCount] = useState(0);

  useEffect(() => {
    const fetchDue = async () => {
      try {
        const cards = await cardsApi.due();
        setQueue(cards);
      } catch (err) {
        console.error("Erro ao buscar cards devidos:", err);
        setError("Não foi possível carregar seus cards para revisão.");
      } finally {
        setLoading(false);
      }
    };
    fetchDue();
  }, []);

  const currentCard = queue[currentIndex];
  const progress = useMemo(
    () =>
      queue.length === 0
        ? 0
        : Math.round((showedCount / queue.length) * 100),
    [showedCount, queue.length]
  );

  function flip() {
    if (phase === "front") setPhase("back");
  }

  async function rate(rating: ReviewRating) {
    if (!currentCard || submitting) return;
    setSubmitting(true);
    const startedAt = Date.now();
    try {
      const result = await cardsApi.review(
        currentCard.id,
        rating,
        Date.now() - startedAt
      );
      setLastFeedback(result.review.feedback_text);
      setFeedbackSource(result.review.feedback_source);
      setPhase("feedback");
    } catch (err) {
      console.error("Erro ao registrar review:", err);
      setError("Não foi possível salvar sua resposta. Tente novamente.");
    } finally {
      setSubmitting(false);
    }
  }

  function next() {
    setLastFeedback(null);
    setFeedbackSource("");
    setShowedCount((c) => c + 1);
    if (currentIndex + 1 >= queue.length) {
      setPhase("finished");
    } else {
      setCurrentIndex((i) => i + 1);
      setPhase("front");
    }
  }

  // Atalhos de teclado: 1/2/3/4 para avaliar, Espaço pra virar/próximo.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (submitting || phase === "finished") return;
      if (phase === "front" && (e.code === "Space" || e.code === "Enter")) {
        e.preventDefault();
        flip();
        return;
      }
      if (phase === "back" && ["1", "2", "3", "4"].includes(e.key)) {
        e.preventDefault();
        const r = Number(e.key) as ReviewRating;
        rate(r);
        return;
      }
      if (phase === "feedback" && (e.code === "Space" || e.code === "Enter")) {
        e.preventDefault();
        next();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, submitting, currentCard]);

  if (loading) {
    return (
      <AppShell>
        <div className="flex min-h-[400px] items-center justify-center text-muted-foreground">
          <Loader2 className="size-6 stroke-2 animate-spin" />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <Card className="border-destructive/50">
          <CardContent className="pt-6 text-destructive">{error}</CardContent>
        </Card>
      </AppShell>
    );
  }

  if (queue.length === 0 || phase === "finished") {
    return <ReviewFinished count={showedCount} onBack={() => navigate("/dashboard")} />;
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        {/* Header com progresso */}
        <div className="mb-6 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/dashboard")}
            aria-label="Voltar ao dashboard"
          >
            <ArrowLeft className="size-4 stroke-2" />
          </Button>
          <div className="flex-1">
            <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Card {currentIndex + 1} de {queue.length}
              </span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300 ease-in-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Cartão da pergunta */}
        <Card
          className={cn(
            "min-h-[320px] cursor-pointer select-none transition-all",
            phase === "front"
              ? "hover:border-primary/30 hover:shadow-md"
              : ""
          )}
          onClick={phase === "front" ? flip : undefined}
        >
          <CardContent className="flex min-h-[320px] flex-col items-center justify-center gap-3 p-8 text-center">
            {phase === "front" ? (
              <>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Pergunta
                </p>
                <p className="whitespace-pre-wrap text-xl font-medium">
                  {currentCard.front}
                </p>
                <p className="absolute bottom-4 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <RotateCcw className="size-3" />
                  Clique ou Espaço para revelar
                </p>
              </>
            ) : (
              <>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Resposta
                </p>
                <p className="whitespace-pre-wrap text-2xl font-semibold">
                  {currentCard.back}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Feedback IA (após avaliar) */}
        {phase === "feedback" && lastFeedback ? (
          <Card className="mt-4 border-primary/30 bg-accent/40">
            <CardContent className="flex gap-3 p-4">
              <Sparkles className="mt-0.5 size-5 shrink-0 stroke-2 text-primary" />
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-primary">
                    Feedback
                  </span>
                  <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                    {feedbackSource.startsWith("ai")
                      ? "IA"
                      : "heurística"}
                  </span>
                </div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {lastFeedback}
                </p>
                <button
                  type="button"
                  className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                  onClick={next}
                >
                  Continuar <span className="rounded border border-border px-1 py-0.5">Espaço</span>
                </button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* Botões de avaliação */}
        {phase === "back" ? (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {RATING_BUTTONS.map((b) => (
              <button
                key={b.rating}
                type="button"
                disabled={submitting}
                onClick={() => rate(b.rating)}
                className={cn(
                  "flex h-12 flex-col items-center justify-center gap-0.5 rounded-md text-sm font-semibold shadow-sm transition-all disabled:opacity-50 disabled:pointer-events-none",
                  b.className
                )}
              >
                <span>{b.label}</span>
                <span className="text-[10px] opacity-80">{b.shortcut}</span>
              </button>
            ))}
          </div>
        ) : phase === "feedback" ? (
          <div className="mt-4">
            <Button onClick={next} className="w-full" disabled={submitting}>
              Próximo card
            </Button>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function ReviewFinished({ count, onBack }: { count: number; onBack: () => void }) {
  return (
    <AppShell>
      <div className="mx-auto max-w-md pt-12">
        <Card>
          <CardContent className="flex flex-col items-center gap-4 pt-12 pb-12 text-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-success/15 text-success">
              <CheckCircle2 className="size-8 stroke-2" />
            </div>
            <div className="space-y-1">
              <p className="text-xl font-semibold">Sessão concluída!</p>
              <p className="text-sm text-muted-foreground">
                Você revisou {count} {count === 1 ? "card" : "cards"}. Continue
                assim para manter sua sequência.
              </p>
            </div>
            <Button onClick={onBack} variant="outline">
              <ArrowLeft className="size-4 stroke-2" />
              Voltar ao dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
