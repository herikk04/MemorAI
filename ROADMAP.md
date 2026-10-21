# Roadmap

Estado por sprint. O detalhe arquitetural vive em [`docs/SDD.md`](docs/SDD.md).

## Concluído

| Sprint | Entrega |
| --- | --- |
| 0 | Fundação: backend modular, settings por ambiente, Docker Compose, `requirements.txt` |
| 1 | SRS: campos no `Card`, `Review`, schedulers FSRS-lite e SM-2, `POST /cards/{id}/review/` |
| 1.5 | Auth JWT com rotação e blacklist; decks e cards escopados por dono |
| 2 | Núcleo de IA: orquestrador, clients (OpenAI, Anthropic, Ollama, mock), prompts YAML, guardrails de PII, cota diária |
| 3 | RAG: embeddings, pgvector, `POST /ai/search/` |
| 4 | Analytics assíncrono: relatório e sugestões via Celery |
| 5 | Frontend React + TypeScript: login, cadastro, dashboard, deck, revisão, relatório |
| 6 | Loop de estudo de ponta a ponta: cadastro, fila com cards novos, `GET /dashboard/` com dados reais, throttle de auth |
| 7 | Geração assistida de cards: `POST /ai/generate-cards/` e diálogo "Gerar com IA" |
| 8 | Busca semântica na UI: diálogo no `AppShell` (Ctrl/Cmd+K) sobre `/ai/search/` |
| Infra | Imagens de produção (gunicorn, whitenoise, nginx), `docker-compose.prod.yml`, CI no GitHub Actions |

## Próximos passos

1. **Importar e exportar Anki** (`.apkg` ou CSV). O AnkiConnect só funciona na máquina do aluno, então o arquivo é o caminho mais viável para o produto hospedado.
2. **FSRS completo** (biblioteca `fsrs`) no lugar do agendador compacto, com parâmetros por usuário.
3. **Revisão por deck** e reinserção na fila dos cards avaliados como "Again".
4. **Gamificação**: XP, conquistas e ranking semanal (o streak já existe no dashboard).
5. **Lembretes**: usar `Profile.notify_review_due` para notificar cards vencidos.
6. **Tokens fora do `sessionStorage`**: cookie `httpOnly` para o refresh token.
7. **Módulos de aprendizado**, execução de código e comunidade (visão de longo prazo do README).
