# MemorAI Design System

Stack: **Tailwind v4** (CSS-first) + **shadcn/ui** (Radix primitives) + **TypeScript**.

A pasta `design/` documenta o sistema visual e serve de referência rápida.
A implementação vive no frontend em `frontend/src/styles/` e `frontend/src/components/ui/`.

## Princípios

1. **Identidade própria, não template de IA.** Sem gradientes violetas e sem
   "hero de produto SaaS" — a cara é editorial (claro) e técnica/IDE (escuro).
2. **Tailwind v4 CSS-first.** Tokens como variáveis CSS em `globals.css`; não há
   `tailwind.config.js`. Use `@theme` para adicionar tokens.
3. **shadcn/ui (componentes copiados).** Os componentes vivem no repo em
   `src/components/ui/`. Edite à vontade — não são dependências externas.
4. **Acessibilidade first.** Tudo sobre Radix: focus rings, ARIA, navegação por
   teclado nativa.
5. **Dark mode como cidadão de primeira classe** — não decorativo.

## Tokens semânticos

Definidos em `frontend/src/styles/globals.css` e mapeados para o Tailwind via
`@theme`. Componha sempre com as cores semânticas — **nunca** com cores hex diretas.

| Token                  | Uso                                    |
| ---------------------- | -------------------------------------- |
| `bg-background`        | Fundo global da aplicação              |
| `text-foreground`      | Texto base                             |
| `bg-card`              | Superfície elevada (cards, panels)    |
| `text-muted-foreground`| Texto secundário / disabled            |
| `bg-primary`           | Ação principal (CTA)                  |
| `bg-secondary`         | Ação secundária                        |
| `bg-accent`            | Hover destaque                         |
| `bg-destructive`       | Erro / ação destrutiva                 |
| `border-border`        | Bordas                                 |
| `ring-ring`            | Focus ring                             |

Os tokens _trocam de valor_ entre `.light` e `.dark` automaticamente; o seletor
`* { border-color: var(--border) }` em `globals.css` garante bordas consistentes.

## Componentes disponíveis

Em `frontend/src/components/ui/`:

| Componente | Arquivo       | Notas                                            |
| ---------- | ------------- | ------------------------------------------------ |
| `Button`   | `button.tsx`  | variants: default/destructive/outline/secondary/ghost/link; sizes: default/sm/lg/icon |
| `Card`     | `card.tsx`    | composto: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` |
| `Badge`    | `badge.tsx`   | variants: default/secondary/destructive/outline/success |
| `Input`    | `input.tsx`   | input de formulário estilizado                   |
| `Tooltip`  | `tooltip.tsx` | `Tooltip`, `TooltipTrigger`, `TooltipContent`, `TooltipProvider` |

## Layout e tema

- `AppShell` (`components/layout/app-shell.tsx`): header sticky com logo MemorAI
  + theme toggle + footer. Envolva páginas com `<AppShell>...</AppShell>`.
- `ThemeProvider` (`components/theme/theme-provider.tsx`): aplica `.light`/`.dark`
  no `<html>`, persiste em `localStorage["memorai-theme"]` e respeita a preferência
  do sistema quando o tema é `"system"`.
- `useTheme()`: hook para ler `{ theme, resolvedTheme, setTheme, toggle }`.

```tsx
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";

export default function MyPage() {
  return (
    <AppShell>
      <Card>
        <CardContent>Conteúdo</CardContent>
      </Card>
    </AppShell>
  );
}
```

## Adicionar novo componente shadcn

1. `npm install @radix-ui/react-<primitive> --legacy-peer-deps`
2. Copie o componente do catálogo shadcn para `src/components/ui/<nome>.tsx`.
3. Ajuste o import do `cn` para `@/lib/utils` se necessário.

## Scripts

```bash
npm start        # dev server (porta 3000)
npm run build    # build produção
npm run typecheck # tsc --noEmit
npm test         # jest
```

## Não usar

- `tailwind.config.js` (Tailwind v4 mudou para CSS-first via `@theme`).
- Cores hex literais em componentes (`#4338ca` etc.) — use sempre tokens.
- `import * as React from "react"` em componentes novos (React 19 JSX runtime
  não precisa disso; `tsc` com `noUnusedLocals` reclamará).
