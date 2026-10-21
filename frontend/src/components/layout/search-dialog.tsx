import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";
import { Loader2, Search } from "lucide-react";

import { aiApi, type SearchHit } from "@/api/ai";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface SearchDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Busca semântica nos cards do usuário (POST /ai/search/).
 * Dispara no Enter (cada busca gera um embedding, que conta na cota de IA).
 */
export function SearchDialog({ open, onOpenChange }: SearchDialogProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setHits(null);
      setError(null);
    }
  }, [open]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setError(null);
    try {
      const res = await aiApi.search(q);
      setHits(res.hits);
    } catch (err) {
      setHits(null);
      setError(
        isAxiosError(err) && err.response?.status === 429
          ? "Você atingiu a cota diária de IA."
          : "Não foi possível buscar agora. Tente novamente."
      );
    } finally {
      setBusy(false);
    }
  }

  function open_(hit: SearchHit) {
    onOpenChange(false);
    navigate(`/decks/${hit.deck_id}`);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Buscar nos seus cards</DialogTitle>
          <DialogDescription>
            Busca por significado: descreva o assunto e pressione Enter.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            aria-label="Buscar"
            placeholder="Ex.: como percorrer uma lista com índice"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            maxLength={500}
            autoFocus
          />
          <Button type="submit" disabled={busy || !query.trim()}>
            {busy ? (
              <Loader2 className="size-4 stroke-2 animate-spin" />
            ) : (
              <Search className="size-4 stroke-2" />
            )}
            Buscar
          </Button>
        </form>

        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {hits !== null ? (
          hits.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhum card encontrado.</p>
          ) : (
            <ul className="max-h-80 space-y-2 overflow-y-auto">
              {hits.map((hit) => (
                <li key={hit.card_id}>
                  <button
                    type="button"
                    onClick={() => open_(hit)}
                    className="w-full rounded-md border p-3 text-left text-sm transition-colors hover:bg-accent"
                  >
                    <span className="block font-medium">{hit.front}</span>
                    <span className="line-clamp-2 block text-muted-foreground">
                      {hit.back}
                    </span>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {hit.deck_name}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
