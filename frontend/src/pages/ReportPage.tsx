import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  BarChart3,
  Loader2,
  RefreshCw,
  Brain,
  CalendarClock,
  CheckCircle2,
  AlertOctagon,
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { aiApi, type ReportResponse } from "@/api/ai";

type Status = "idle" | "loading" | "polling" | "success" | "error";

export default function ReportPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<Status>("idle");
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Carrega automaticamente ao montar.
  useEffect(() => {
    void loadReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadReport() {
    setStatus("loading");
    setError(null);
    setReport(null);
    try {
      const r = await aiApi.fetchReport({
        language: "pt",
        maxAttempts: 12,
        onPending: () => {
          setStatus("polling");
          setPollCount((c) => c + 1);
        },
      });
      setReport(r);
      setStatus("success");
    } catch (err) {
      console.error("Falha ao gerar relatório:", err);
      setError(
        err instanceof Error && err.message === "report-task-failed"
          ? "A tarefa de geração falhou no backend."
          : "Não foi possível gerar o relatório agora. Tente novamente."
      );
      setStatus("error");
    }
  }

  const isLoading = status === "loading" || status === "polling";

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

      <div className="mx-auto max-w-3xl">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight sm:text-3xl">
              <BarChart3 className="size-6 stroke-2 text-primary" />
              Relatório de evolução
            </h1>
            <p className="text-sm text-muted-foreground">
              Análise do seu progresso gerada por IA.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={loadReport}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="size-4 stroke-2 animate-spin" />
            ) : (
              <RefreshCw className="size-4 stroke-2" />
            )}
            Atualizar
          </Button>
        </div>

        {/* Estados */}
        {isLoading ? (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
              <Loader2 className="size-8 stroke-2 animate-spin text-primary" />
              <div className="space-y-1">
                <p className="font-medium">
                  {status === "polling"
                    ? "Gerando relatório com IA..."
                    : "Carregando..."}
                </p>
                {pollCount > 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Aguardando o servidor ({pollCount})
                  </p>
                ) : null}
              </div>
            </CardContent>
          </Card>
        ) : error ? (
          <Card className="border-destructive/50">
            <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
                <AlertOctagon className="size-6 stroke-2" />
              </div>
              <p className="font-medium">Não foi possível gerar o relatório</p>
              <p className="text-sm text-muted-foreground max-w-sm">{error}</p>
              <Button onClick={loadReport}>
                <RefreshCw className="size-4 stroke-2" />
                Tentar de novo
              </Button>
            </CardContent>
          </Card>
        ) : report ? (
          <div className="space-y-6">
            {/* Métricas */}
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:gap-4">
              <Metric
                icon={<CheckCircle2 className="size-4 stroke-2" />}
                label="Total de revisões"
                value={String(report.metrics.total_reviews)}
              />
              <Metric
                icon={<AlertOctagon className="size-4 stroke-2" />}
                label="Lapses"
                value={String(report.metrics.total_lapses)}
              />
              <Metric
                icon={<BarChart3 className="size-4 stroke-2" />}
                label="Média de reps"
                value={report.metrics.avg_reps.toFixed(1)}
              />
              <Metric
                icon={<CalendarClock className="size-4 stroke-2" />}
                label="Última revisão"
                value={
                  report.metrics.last_review_at
                    ? new Date(report.metrics.last_review_at).toLocaleDateString("pt-BR")
                    : "—"
                }
              />
            </div>

            {/* Texto descritivo da IA */}
            <Card className="border-primary/30 bg-accent/40">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Brain className="size-5 stroke-2 text-primary" />
                  <span className="text-sm font-semibold uppercase tracking-wider text-primary">
                    Análise da IA
                  </span>
                </div>
                <CardDescription>
                  {report.provider} · {report.model}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {report.text}
                </p>
                <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">{report.status}</Badge>
                  <Badge variant="outline">
                    prompt v{report.prompt_version}
                  </Badge>
                  <Badge variant="outline">
                    {report.tokens_in + report.tokens_out} tokens
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <Card>
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
