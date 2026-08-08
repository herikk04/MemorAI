# MemorAI — Design System

> Versão 1.0 · Agosto 2026  
> Stack: React + TypeScript + Tailwind CSS v4

---

## 0. Princípios

O MemorAI é um app de repetição espaçada para estudantes (vestibular, concursos, idiomas). O design deve transmitir **progresso, clareza e motivação** — sem parecer um produto de IA genérico.

| Princípio | Significado prático |
|-----------|-------------------|
| **Amigável mas sério** | Não infantil, não corporativo. Fala com quem estuda de verdade. |
| **Conteúdo em primeiro lugar** | UI discreta. O deck, o card e o progresso são protagonistas. |
| **Feedback imediato** | Cada ação retorna uma resposta visual clara (hover, active, success). |
| **Consistência radical** | Tokens → Componentes → Páginas. Nunca valores mágicos inline. |

### Anti-padrões (o que evitar)
- Roxo/violeta como cor primária (clichê de IA)
- Gradientes forçados em elementos interativos
- Ícones de linha fina (stroke-width < 1.5) — usar stroke-width="2" no Lucide
- Sombras excessivas (mais de 2 camadas)
- Texto em CAPS LOCK em destaque (só em labels de seção)

---

## 1. Paleta de Cores

### Filosofia
A cor primária é **verde-esmeralda** (emerald). Remete a progresso, saúde e aprendizado — sem os clichês de IA. O restante da paleta é construída sobre tons **neutros frios** (slate), mantendo o app sóbrio e focado no conteúdo.

### 1.1 Primitivos (tokens base)

Estes são os valores concretos. Nunca use eles diretamente no JSX — use os tokens semânticos abaixo.

```
Emerald (primária)
  --emerald-50:  #ecfdf5
  --emerald-100: #d1fae5
  --emerald-200: #a7f3d0
  --emerald-300: #6ee7b7
  --emerald-400: #34d399
  --emerald-500: #10b981
  --emerald-600: #059669   ← brand / primary principal
  --emerald-700: #047857
  --emerald-800: #065f46
  --emerald-900: #064e3b
  --emerald-950: #022c22

Slate (neutros)
  --slate-50:  #f8fafc
  --slate-100: #f1f5f9
  --slate-200: #e2e8f0
  --slate-300: #cbd5e1
  --slate-400: #94a3b8
  --slate-500: #64748b
  --slate-600: #475569
  --slate-700: #334155
  --slate-800: #1e293b
  --slate-850: #172032   ← custom (dark backgrounds)
  --slate-900: #0f172a
  --slate-950: #020617

Amber (atenção / streak)
  --amber-400: #fbbf24
  --amber-500: #f59e0b
  --amber-600: #d97706

Red (erro / destrutivo)
  --red-400: #f87171
  --red-500: #ef4444
  --red-600: #dc2626
```

### 1.2 Tokens semânticos — Tema Claro

| Token CSS | Valor | Uso |
|-----------|-------|-----|
| `--background` | `#f8faf8` | Fundo da página |
| `--foreground` | `#111816` | Texto principal |
| `--card` | `#ffffff` | Fundo de cards |
| `--card-foreground` | `#111816` | Texto dentro de cards |
| `--popover` | `#ffffff` | Dropdowns, tooltips |
| `--popover-foreground` | `#111816` | Texto de popover |
| `--primary` | `#059669` | Ações principais, botões CTA |
| `--primary-foreground` | `#ffffff` | Texto sobre primário |
| `--secondary` | `#ecfdf5` | Fundo de elementos secundários |
| `--secondary-foreground` | `#065f46` | Texto sobre secundário |
| `--muted` | `#f1f5f9` | Fundos neutros, skeletons |
| `--muted-foreground` | `#64748b` | Texto auxiliar, labels |
| `--accent` | `#d1fae5` | Highlights suaves, hover states |
| `--accent-foreground` | `#065f46` | Texto sobre accent |
| `--destructive` | `#dc2626` | Erros, ações perigosas |
| `--destructive-foreground` | `#ffffff` | Texto sobre destrutivo |
| `--warning` | `#f59e0b` | Alertas, streak indicator |
| `--warning-foreground` | `#1a1000` | Texto sobre warning |
| `--success` | `#10b981` | Confirmações, acerto de card |
| `--success-foreground` | `#022c22` | Texto sobre success |
| `--border` | `#e2e8f0` | Bordas padrão |
| `--input` | `#e2e8f0` | Borda de inputs |
| `--ring` | `#059669` | Focus ring |
| `--sidebar` | `#ffffff` | Fundo da sidebar |
| `--sidebar-foreground` | `#1e293b` | Texto da sidebar |
| `--sidebar-accent` | `#f1f5f9` | Hover/ativo na sidebar |
| `--sidebar-accent-foreground` | `#111816` | Texto ativo na sidebar |
| `--sidebar-border` | `#e2e8f0` | Bordas da sidebar |

### 1.3 Tokens semânticos — Tema Escuro

| Token CSS | Valor | Uso |
|-----------|-------|-----|
| `--background` | `#0c1210` | Fundo da página |
| `--foreground` | `#e2f0ea` | Texto principal |
| `--card` | `#121a16` | Fundo de cards |
| `--card-foreground` | `#e2f0ea` | Texto dentro de cards |
| `--popover` | `#121a16` | Dropdowns, tooltips |
| `--popover-foreground` | `#e2f0ea` | Texto de popover |
| `--primary` | `#34d399` | Ações principais (mais claro no dark) |
| `--primary-foreground` | `#022c22` | Texto sobre primário |
| `--secondary` | `#1a2e24` | Fundo de elementos secundários |
| `--secondary-foreground` | `#6ee7b7` | Texto sobre secundário |
| `--muted` | `#172032` | Fundos neutros, skeletons |
| `--muted-foreground` | `#8ba89a` | Texto auxiliar, labels |
| `--accent` | `#1e3028` | Highlights suaves, hover states |
| `--accent-foreground` | `#6ee7b7` | Texto sobre accent |
| `--destructive` | `#f87171` | Erros |
| `--destructive-foreground` | `#0c1210` | Texto sobre destrutivo |
| `--warning` | `#fbbf24` | Alertas, streak |
| `--warning-foreground` | `#0c1210` | Texto sobre warning |
| `--success` | `#34d399` | Confirmações |
| `--success-foreground` | `#022c22` | Texto sobre success |
| `--border` | `#1e3028` | Bordas padrão |
| `--input` | `#1e3028` | Borda de inputs |
| `--ring` | `#34d399` | Focus ring |
| `--sidebar` | `#0a100d` | Fundo da sidebar |
| `--sidebar-foreground` | `#c4ddd3` | Texto da sidebar |
| `--sidebar-accent` | `#172032` | Hover/ativo na sidebar |
| `--sidebar-accent-foreground` | `#e2f0ea` | Texto ativo na sidebar |
| `--sidebar-border` | `#1a2e24` | Bordas da sidebar |

---

## 2. Tipografia

### Fontes

| Papel | Fonte | Fallback |
|-------|-------|---------|
| **Interface (sans)** | `Inter` | `Segoe UI`, `system-ui`, sans-serif |
| **Código/mono** | `JetBrains Mono` | `Fira Code`, `ui-monospace`, monospace |

> Não usar fonte serif no app. Reservado para landing page futura.

### Escala tipográfica

```
xs:   0.75rem  (12px) · lh: 1rem      — labels, badges, metadata
sm:   0.875rem (14px) · lh: 1.25rem   — textos auxiliares, descrições
base: 1rem     (16px) · lh: 1.5rem    — corpo de texto padrão
lg:   1.125rem (18px) · lh: 1.75rem   — subtítulos de seção
xl:   1.25rem  (20px) · lh: 1.75rem   — títulos de card
2xl:  1.5rem   (24px) · lh: 2rem      — títulos de página (mobile)
3xl:  1.875rem (30px) · lh: 2.25rem   — títulos de página (desktop)
4xl:  2.25rem  (36px) · lh: 2.5rem    — hero (landing page)
```

### Pesos

| Peso | Classe Tailwind | Uso |
|------|-----------------|-----|
| 400 Regular | `font-normal` | Corpo de texto, descrições longas |
| 500 Medium | `font-medium` | Labels, itens de nav, metadata importante |
| 600 SemiBold | `font-semibold` | Títulos de card, valores de métricas, botões |
| 700 Bold | `font-bold` | Títulos de página (h1, h2) |

### Padrões de uso

```
h1 (título da página):   text-2xl sm:text-3xl font-bold tracking-tight
h2 (título de seção):    text-sm font-semibold uppercase tracking-wider text-muted-foreground
h3 (título de card):     text-base font-semibold
p  (corpo):              text-sm text-foreground leading-relaxed
caption / label:         text-xs font-medium text-muted-foreground
```

---

## 3. Espaçamento

Usar o sistema de grid de 4px do Tailwind. **Nunca usar valores arbitrários** (ex: `px-[13px]`).

```
1 →  4px   gap mínimo entre elementos inline
2 →  8px   padding interno de badges, gap entre ícone e texto
3 → 12px   gap padrão dentro de componentes pequenos
4 → 16px   padding interno de cards compactos, gap de listas
5 → 20px   padding padrão de cards
6 → 24px   padding de CardHeader/CardContent padrão
8 → 32px   espaço entre seções dentro de uma página
10→ 40px   margem entre blocos maiores da página
12→ 48px   padding vertical de seções grandes
```

### Padding de página

| Breakpoint | Lateral | Vertical |
|-----------|---------|---------|
| Mobile (< lg) | `px-4` | `py-6` |
| Desktop (>= lg) | `px-8` | `py-8` |

---

## 4. Border Radius

```
--radius:      0.5rem   (8px)   padrão
--radius-md:   0.375rem (6px)   calc(var(--radius) - 2px)
--radius-sm:   0.25rem  (4px)   calc(var(--radius) - 4px)
--radius-lg:   0.75rem  (12px)  cards principais, modals
--radius-xl:   1rem     (16px)  elementos de destaque
--radius-full: 9999px           badges, avatares, pills
```

**Regra:** Cards = `rounded-xl` | Buttons = `rounded-md` | Nunca misturar.

---

## 5. Sombras

```
shadow-xs:  0 1px 2px 0 rgb(0 0 0 / 0.05)           inputs no focus
shadow-sm:  0 1px 3px 0 rgb(0 0 0 / 0.10)           cards padrão
shadow-md:  0 4px 6px -1px rgb(0 0 0 / 0.10)        cards em hover
shadow-lg:  0 10px 15px -3px rgb(0 0 0 / 0.10)      modals, popovers
```

> No dark mode: usar bordas em vez de sombras quando possível.

---

## 6. Componentes

### 6.1 Button

| Variante | Quando usar |
|----------|-------------|
| `default` | CTA principal. Máx 1 por tela visível. |
| `secondary` | Ação secundária, menos urgente. |
| `outline` | Ações neutras, opções alternativas. |
| `ghost` | Navegação interna, ações repetitivas. |
| `destructive` | Deletar deck, remover card. |
| `link` | Inline em texto. |

| Size | Altura | Uso |
|------|--------|-----|
| `sm` | 32px | Dentro de cards, tabelas |
| `default` | 36px | Contexto geral |
| `lg` | 40px | Hero, empty states, CTAs de página |
| `icon` | 36×36px | Ação isolada sem label |

**Regras:**
- Ícone: `size-4` (16px) — nunca menor
- Lucide `strokeWidth` padrão = 2 — nunca 1 ou 1.5
- Disabled: `opacity-50 pointer-events-none`

### 6.2 Card

```
Base:      rounded-xl border bg-card text-card-foreground shadow-sm
Hover:     transition-all hover:border-primary/30 hover:shadow-md hover:-translate-y-0.5
Destaque:  border-primary/40
Erro:      border-destructive/50
Vazio:     border-dashed
```

Anatomia: Card > CardHeader > (CardTitle + CardDescription) + CardContent + CardFooter

### 6.3 Badge

| Variante | Uso |
|----------|-----|
| `default` | Contagem urgente ("24 p/ hoje") |
| `secondary` | Tags, categorias |
| `success` | Estado positivo ("em dia") |
| `warning` | Atenção necessária |
| `destructive` | Erro, urgência |
| `outline` | Informativo neutro |

### 6.4 Input

```
h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm
transition-colors placeholder:text-muted-foreground
focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring
disabled:cursor-not-allowed disabled:opacity-50
```

### 6.5 Progress Bar

```
Container: h-1.5 w-full overflow-hidden rounded-full bg-muted
Fill:      h-full rounded-full bg-primary transition-all duration-300
```

---

## 7. Ícones

**Biblioteca:** Lucide React

| Regra | Detalhe |
|-------|---------|
| `strokeWidth` | Sempre 2. Nunca 1 ou 1.5. |
| Tamanhos | `size-4` (inline), `size-5` (container), `size-6` (destaque) |
| Cor | `currentColor` — não aplicar cor diretamente |

### Mapeamento semântico

| Contexto | Ícone |
|---------|-------|
| Dashboard | `LayoutDashboard` |
| Decks / Cards | `Layers` |
| Revisão do dia | `Flame` |
| Progresso / Streak | `TrendingUp` |
| Calendário | `CalendarClock` |
| Concluído / Acerto | `CheckCircle2` |
| Ranking | `Trophy` |
| Comunidade | `Users` |
| Configurações | `Settings` |
| Busca | `Search` |
| Adicionar | `Plus` |
| Editar | `Pencil` |
| Deletar | `Trash2` |
| App Logo | `Brain` |
| Tema | `Sun` / `Moon` |
| Fechar | `X` |
| Alerta | `AlertTriangle` |
| Info | `Info` |

---

## 8. Layout

### Shell do App

```
Sidebar: w-60 (240px), sticky, h-screen, hidden < lg
Header:  h-14 (56px), sticky top-0, z-30, blur backdrop
Main:    px-4 py-6 lg:px-8 lg:py-8
```

### Grids

```
Deck cards:  grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4
Métricas:    grid-cols-2 sm:grid-cols-4 gap-3 lg:gap-4
```

---

## 9. Motion & Animações

| Elemento | Transição | Duração |
|---------|-----------|---------|
| Hover de card | translate-y + shadow | 150ms ease-out |
| Hover de botão | opacity/background | 150ms |
| Progress bar | width | 300ms ease-in-out |
| Tooltips | fade | 100ms |
| Modals | fade + scale | 150ms ease-out |
| Theme toggle | rotate | 200ms ease-in-out |

**Regra:** Interações <= 200ms. Conteúdo <= 300ms. Evitar `transition-all` em elementos com muitas propriedades.

---

## 10. Estados de UI

| Estado | Tratamento |
|--------|-----------|
| Default | Estilo base |
| Hover | Leve mudança de fundo/borda/sombra |
| Focus | `ring-2 ring-ring ring-offset-2` — nunca remover sem substituir |
| Disabled | `opacity-50 cursor-not-allowed pointer-events-none` |
| Loading | Skeleton ou spinner — nunca deixar vazio |
| Empty | Ícone + texto + CTA (ver padrão abaixo) |
| Error | Borda destructive + mensagem de texto |

### Padrão Empty State

```tsx
<Card className="border-dashed">
  <CardContent className="flex flex-col items-center gap-3 pt-12 pb-12 text-center">
    <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
      <IconRelevante className="size-6" />
    </div>
    <div className="space-y-1">
      <p className="font-medium">Título do estado vazio</p>
      <p className="text-sm text-muted-foreground">
        Descrição curta e encorajadora.
      </p>
    </div>
    <Button>
      <Plus className="size-4" />
      Ação principal
    </Button>
  </CardContent>
</Card>
```

---

## 11. Padrões de Domínio (Flashcards)

### Cores de performance (respostas)

| Resultado | Cor | Token |
|-----------|-----|-------|
| Não lembrei (Again) | Vermelho | `--destructive` |
| Difícil (Hard) | Âmbar | `--warning` |
| Bom (Good) | Verde | `--primary` |
| Fácil (Easy) | Esmeralda claro | `--success` |

### Streak

- Ícone: `Flame` com `text-amber-500` — nunca usar a cor primária verde
- Badge: variante `warning`

### Progresso de Deck

- Barra: `bg-primary` sobre `bg-muted`
- Não mostrar 0% como barra — esconder ou exibir "Novo deck"

---

## 12. Acessibilidade

| Regra | Implementação |
|-------|--------------|
| Contraste | WCAG AA (4.5:1 texto, 3:1 UI) |
| Focus | `focus-visible:ring-2 focus-visible:ring-ring` |
| Botões ícone | `aria-label` obrigatório |
| Estados | `aria-disabled`, `aria-busy`, `role="status"` |
| Headings | Uma h1 por página, sem pular níveis |
| Cor como único sinal | Proibido — sempre acompanhar com texto ou ícone |

---

## 13. Convenções de Código

### Estrutura de arquivos

```
src/
  components/
    ui/          ← Primitivos (button, card, badge, input...)
    layout/      ← Estruturais (app-shell, header, sidebar...)
    theme/       ← Theme provider e toggle
    [feature]/   ← Domínio (deck-card, review-session...)
  pages/         ← DashboardPage, ReviewPage...
  styles/
    globals.css  ← Tokens e reset
  lib/
    utils.ts     ← cn(), helpers
  api/           ← Chamadas de API
```

### Nomenclatura

| Tipo | Convenção | Exemplo |
|------|-----------|---------|
| Componentes React | PascalCase | `DeckCard.tsx` |
| Páginas | PascalCase + sufixo Page | `DashboardPage.tsx` |
| Hooks | camelCase + use | `useDecks.ts` |
| Utilitários | kebab-case | `format-date.ts` |

### Regra do cn()

```tsx
// Sempre usar cn() para combinar classes
className={cn("base-class", condition && "conditional-class", className)}

// Nunca concatenar strings diretamente
className={`base-class ${condition ? "cond" : ""}`}  // proibido
```

---

## 14. Checklist — Novo Componente

- [ ] Usa tokens semânticos (sem cores hardcoded)
- [ ] Tem todos os estados: default, hover, focus, disabled
- [ ] Aceita `className` como prop
- [ ] Usa `cn()` para composição de classes
- [ ] Ícones com `size-4/5` e `strokeWidth={2}`
- [ ] Funciona em dark mode
- [ ] Tem `displayName` se for `forwardRef`
- [ ] Responsivo: testado em 375px e 1440px

---

## 15. Referências de Estilo

| Produto | O que inspiramos |
|---------|-----------------|
| **Linear** | Dark mode técnico, sidebar limpa |
| **Duolingo (pro)** | Motivação sem infantilidade |
| **Notion** | Hierarquia tipográfica, espaçamento editorial |
| **Cal.com** | Honesto, sem glossy excessivo |
| **Raycast** | Densidade de informação, paleta escura elegante |

### O que evitar

| Estilo | Por quê |
|--------|---------|
| ChatGPT / Claude UI | Roxo + gradientes = clichê de IA |
| Material Design 3 | Muito colorido, sem personalidade da marca |
| Bootstrap padrão | Sem identidade visual |
