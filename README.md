# MemorAI

Plataforma de ensino de programação fundamentada na **Curva do Esquecimento de Ebbinghaus**, que aplica **repetição espaçada (SRS)** para maximizar a retenção de conhecimento — via flashcards, módulos estruturados, gamificação e feedback inteligente.

> Status atual: **MVP em construção**. Backend Django REST + auth JWT ativos; camada de IA isolada em scaffold; frontend em scaffolding. Veja [`docs/SDD.md`](docs/SDD.md) como fonte única de verdade arquitetural.

---

## Sumário

- [Visão](#visão)
- [Público-alvo](#público-alvo)
- [Metodologia](#metodologia)
- [Funcionalidades previstas](#funcionalidades-previstas)
- [Stack](#stack)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar](#como-rodar)
- [Roadmap](#roadmap)
- [Documentação](#documentação)
- [Como contribuir](#como-contribuir)
- [Licença](#licença)

## Visão

Aprender programação é luta contra o esquecimento. O MemorAI aplica o algoritmo de Ebbinghaus (com path futuro para o scheduler modern FSRS e integração opcional com o Anki via AnkiConnect) para agendar revisões no ponto certo da curva e entregar — junto ao conteúdo — feedback gerado por IA, módulos práticos e gamificação que sustenta a consistência.

O projeto trata a IA como **camada isolada de serviço** (ver `docs/SDD.md` §3): prompts versionados, adaptadores pluggáveis de provedores (OpenAI/Anthropic/Ollama), guardrails de custo/PII e fallback determinístico — nunca como adorno.

## Público-alvo

- Estudantes de programação iniciantes e avançados.
- Profissionais em upskilling técnico.
- Instituições de ensino buscando soluções interativas.
- Empresas treinando desenvolvedores.

## Metodologia

- **Curva do Esquecimento de Ebbinghaus**: revisões programadas para maximizar retenção.
- **Repetição espaçada (SRS)**: scheduler pluggável (FSRS/SM2) em `flashcards/services/scheduler.py` (caminho planejado), com AnkiConnect como canal opcional.
- **Feedback inteligente**: sugestões de reforço por conteúdo de maior dificuldade, via fluxos de IA.
- **Microlearning**: conteúdos curtos e direcionados.
- **Gamificação**: pontuação por consistência, conquistas, rankings semanais.
- **Monitoramento de progresso**: relatórios de evolução personalizados por aluno.

## Funcionalidades previstas

- **Criação e gerenciamento de flashcards** — cards personalizados (código, imagens, explicações), decks compartilháveis, integração opcional com Anki.
- **Módulos de aprendizado estruturados** — cursos por dificuldade e temas, exercícios interativos, certificados de conclusão.
- **Gamificação** — pontuação por consistência, conquistas, desafios e rankings semanais.
- **Dashboard de acompanhamento** — progresso e desempenho, sugestões de revisão, lembretes inteligentes.
- **Integração com código e IDEs** — ambientes interativos para executar código na plataforma; integração com GitHub para submissão de projetos.
- **Comunidade** — fórum de dúvidas, sessões de Q&A, grupos de estudo e mentorias.

## Stack

**Backend (ativo):**
- Python 3 · Django 5.2 · Django REST Framework 3.16
- SQLite em dev · PostgreSQL 16 + pgvector em prod (via Docker)
- `djangorestframework-simplejwt` (auth JWT) · `drf-spectacular` (OpenAPI) · `django-cors-headers`
- Celery 5.4 + Redis 7 (jobs assíncronos de IA analítica) — pronto no compose
- LLM clients (OpenAI 1.40 / Anthropic 0.34) — reservados para a camada de IA
- `django-environ` (secrets), `structlog` (observabilidade)

**Frontend / mobile:** scaffolding (ver `frontend/` e `mobile/`).

**Infra:** Docker Compose (`db` + `redis` + `web` + `worker` + `frontend`).

## Estrutura do repositório

```
memorai/
├── README.md                    # este arquivo
├── ROADMAP.md                   # planejamento por sprints
├── CONTRIBUTING.md
├── LICENSE
├── docker-compose.yml           # stack local: db+redis+web+worker+frontend
├── .env.example
├── docs/
│   ├── SDD.md                   # Documento de Design de Software (fonte de verdade)
│   ├── architecture.md
│   └── methodology.md
├── design/                      # design system e referências visuais
├── backend/
│   ├── apps/                    # apps Django modulares
│   │   ├── flashcards/          # domínio SRS (Deck/Card/Review)
│   │   ├── users/               # auth JWT + perfis
│   │   └── ai/                  # núcleo de IA isolado (orchestrator/flows/clients/prompts)
│   ├── config/                  # wire-up do Celery e roteador central
│   ├── memorai/                 # projeto Django (settings por ambiente)
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml           # ruff/mypy/pytest
│   └── Dockerfile
├── frontend/
├── mobile/                      # placeholder reservado (Flutter futuro)
├── scripts/                     # utilidades e automação
└── tests/                        # e2e
```

## Como rodar

### Pré-requisitos

- Docker + Docker Compose (ou Python 3.11+ e Node 20+ para rodar localmente sem containers)
- Para IA: chaves de provedor LLM (`OPENAI_API_KEY` etc.) — opcionais em dev (fallback heurístico)

### Com Docker (recomendado)

```bash
# 1. Configure variáveis de ambiente
cp .env.example .env

# 2. Suba a stack completa (db, redis, web, worker, frontend)
docker compose up --build
```

Serviços disponíveis:

| Serviço   | URL / porta          | Observações                                        |
| --------- | -------------------- | -------------------------------------------------- |
| `web`     | http://localhost:8000 | API Django + admin                                 |
| `frontend`| http://localhost:3000 | SPA (em scaffold)                                   |
| `db`      | localhost:5432       | PostgreSQL 16 + pgvector (`memorai:memorai`)      |
| `redis`   | localhost:6379      | cache + broker Celery                              |

### Backend localmente (sem Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Para rodar a fila de IA (opcional): `celery -A memorai worker -l info`.

### Testes

```bash
cd backend && pytest
# ou, dentro do container:
docker compose exec web pytest
```

## Roadmap

Detalhado em [`ROADMAP.md`](ROADMAP.md). Resumo das sprints:

- **Sprint 0 — Fundação** ✅ — backend modular, requirements, docker-compose, settings por ambiente.
- **Sprint 1 — SRS** — campos SRS em `Card`, tabela `Review`, scheduler FSRS, endpoint `/cards/{id}/review/`.
- **Sprint 2 — Núcleo de IA** — app `ai/` com `orchestrator`, `llm_client`, flow de feedback, prompts versionados, `AIEvent`, rate-limit.
- **Sprint 3 — RAG** — embeddings + pgvector + flow de busca semântica.
- **Sprint 4 — Analytics assíncrono** — Celery jobs de relatório e sugestões de revisão.
- **Sprint 5 — Frontend** — router, telas (Review, Report, Login), conexão com endpoints de IA/SRS.
- **Sprint 6 — AnkiConnect** — `flashcards/services/anki.py` + sincronização opcional.

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [`docs/SDD.md`](docs/SDD.md) | **Software Design Document** — arquitetura, módulos de IA, schema de dados, API, trade-offs. |
| [`docs/architecture.md`](docs/architecture.md) | Diagrama lógico e decisão de padrão arquitetural. |
| [`docs/methodology.md`](docs/methodology.md) | Ebbinghaus, FSRS, microlearning. |
| [`ROADMAP.md`](ROADMAP.md) | Planejamento por sprints. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Guia para contribuição. |

## Como contribuir

Leia [`CONTRIBUTING.md`](CONTRIBUTING.md) (a preencher) e [`docs/SDD.md`](docs/SDD.md) antes de tocar em arquitetura. Em especial:

- A IA é **app Django isolada** (`backend/apps/ai/`); toda chamada externa passa por `orchestrator` e `llm_client`. Não introduzir dependências de LLM em outras apps.
- Prompts vivem em `ai/prompts/*.yaml` versionados; nunca strings literais em views.
- Segredos via env, nunca hardcoded (`django-environ`).
- Siga `ruff` + `mypy` (config em `backend/pyproject.toml`).

## Licença

Veja [`LICENSE`](LICENSE).
