import { useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { decksApi, type Deck } from "@/api/decks";
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

interface CreateDeckDialogProps {
  onCreated: (deck: Deck) => void;
  trigger?: React.ReactNode;
}

/**
 * Dialog de criação de deck.
 * Flow: form -> POST /decks/ -> callback onCreated com o deck novo.
 * Sem dependência de toast global (feedback inline no botão).
 */
export function CreateDeckDialog({ onCreated, trigger }: CreateDeckDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const deck = await decksApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      onCreated(deck);
      // Reset + close
      setName("");
      setDescription("");
      setOpen(false);
    } catch (err) {
      console.error("Falha ao criar deck", err);
      setError("Não foi possível criar o deck. Verifique sua conexão.");
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
            Novo deck
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <DialogHeader>
            <DialogTitle>Novo deck</DialogTitle>
            <DialogDescription>
              Crie um deck para organizar seus cards de repetição espaçada.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="deck-name">Nome</Label>
              <Input
                id="deck-name"
                type="text"
                placeholder="Ex.: Python fundamentos"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                maxLength={200}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="deck-description">
                Descrição{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  (opcional)
                </span>
              </Label>
              <Textarea
                id="deck-description"
                placeholder="O que esse deck cobre?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
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
            <Button type="submit" disabled={submitting || !name.trim()}>
              {submitting ? (
                <>
                  <Loader2 className="size-4 stroke-2 animate-spin" />
                  Criando...
                </>
              ) : (
                <>
                  <Plus className="size-4 stroke-2" />
                  Criar deck
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
