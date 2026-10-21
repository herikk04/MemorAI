import { useState } from "react";
import { isAxiosError } from "axios";
import { Loader2, Sparkles } from "lucide-react";

import { aiApi, type GeneratedCard } from "@/api/ai";
import { cardsApi, type Card } from "@/api/cards";
import { tokenService } from "@/lib/token-service";
import { Button } from "@/components/ui/button";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface GenerateCardsDialogProps {
  deckId: number;
  onCreated: (cards: Card[]) => void;
}

function describeError(err: unknown): string {
  if (isAxiosError(err) && err.response?.status === 429) {
    return "Você atingiu a cota diária de IA. Tente novamente amanhã.";
  }
  return "Não foi possível gerar os cards. Tente novamente.";
}

/**
 * Geração assistida: tópico (+ texto base opcional) -> propostas da IA ->
 * o aluno escolhe quais manter -> salva via POST /cards/.
 */
export function GenerateCardsDialog({ deckId, onCreated }: GenerateCardsDialogProps) {
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [count, setCount] = useState(5);
  const [proposals, setProposals] = useState<GeneratedCard[] | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setTopic("");
    setSourceText("");
    setCount(5);
    setProposals(null);
    setSelected(new Set());
    setError(null);
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await aiApi.generateCards({
        topic: topic.trim(),
        source_text: sourceText.trim(),
        count,
        language: tokenService.getUser()?.language ?? "pt",
      });
      if (res.cards.length === 0) {
        setError("A IA não conseguiu gerar cards desta vez. Tente reformular o tópico.");
        return;
      }
      setProposals(res.cards);
      setSelected(new Set(res.cards.map((_, i) => i)));
    } catch (err) {
      setError(describeError(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    if (!proposals) return;
    setError(null);
    setBusy(true);
    try {
      const picked = proposals.filter((_, i) => selected.has(i));
      const created = await Promise.all(
        picked.map((c) => cardsApi.create({ deck: deckId, front: c.front, back: c.back }))
      );
      onCreated(created);
      setOpen(false);
      reset();
    } catch {
      setError("Não foi possível salvar os cards. Tente novamente.");
    } finally {
      setBusy(false);
    }
  }

  function toggle(i: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">
          <Sparkles className="size-4 stroke-2" />
          Gerar com IA
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Gerar cards com IA</DialogTitle>
          <DialogDescription>
            {proposals
              ? "Escolha os cards que quer manter neste deck."
              : "Informe um tópico e, se quiser, cole um texto ou código como base."}
          </DialogDescription>
        </DialogHeader>

        {proposals ? (
          <div className="space-y-4">
            <ul className="max-h-80 space-y-2 overflow-y-auto">
              {proposals.map((c, i) => (
                <li key={i} className="rounded-md border p-3">
                  <label className="flex cursor-pointer items-start gap-3">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={selected.has(i)}
                      onChange={() => toggle(i)}
                    />
                    <span className="space-y-1 text-sm">
                      <span className="block font-medium">{c.front}</span>
                      <span className="block whitespace-pre-wrap text-muted-foreground">
                        {c.back}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => setProposals(null)}
              >
                Voltar
              </Button>
              <Button type="button" disabled={busy || selected.size === 0} onClick={handleSave}>
                {busy ? <Loader2 className="size-4 stroke-2 animate-spin" /> : null}
                Salvar {selected.size} {selected.size === 1 ? "card" : "cards"}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="gen-topic">Tópico</Label>
              <Input
                id="gen-topic"
                placeholder="Ex.: list comprehensions em Python"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                maxLength={200}
                autoFocus
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gen-source">
                Texto base{" "}
                <span className="text-xs font-normal text-muted-foreground">(opcional)</span>
              </Label>
              <Textarea
                id="gen-source"
                placeholder="Cole um trecho de documentação ou código"
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                maxLength={8000}
                rows={5}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gen-count">Quantidade (1 a 10)</Label>
              <Input
                id="gen-count"
                type="number"
                min={1}
                max={10}
                value={count}
                onChange={(e) =>
                  setCount(Math.max(1, Math.min(10, Number(e.target.value) || 1)))
                }
              />
            </div>
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline" disabled={busy}>
                  Cancelar
                </Button>
              </DialogClose>
              <Button type="submit" disabled={busy || !topic.trim()}>
                {busy ? (
                  <>
                    <Loader2 className="size-4 stroke-2 animate-spin" />
                    Gerando...
                  </>
                ) : (
                  <>
                    <Sparkles className="size-4 stroke-2" />
                    Gerar
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
