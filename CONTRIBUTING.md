# Contribuindo

Leia o [`docs/SDD.md`](docs/SDD.md) antes de mexer em arquitetura.

## Ambiente

```bash
# Backend (Python 3.10+)
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (Node 20)
cd frontend
npm ci
npm start
```

Sem chaves de LLM o provedor `mock` é usado automaticamente.

## Antes de abrir um PR

```bash
cd backend  && ruff check apps tests flashcards memorai && pytest -q
cd frontend && npm run typecheck && npm test -- --watchAll=false && npm run build
```

O CI roda exatamente isso.

## Regras do projeto

- **IA isolada**: toda chamada a LLM passa por `apps.ai.services.orchestrator.run_flow`. Nenhum outro app importa clients ou prompts.
- **Prompts** vivem em `backend/apps/ai/prompts/*.yaml` com `version`; mude a versão ao editar. Nunca strings de prompt em views.
- **A IA nunca bloqueia a UX**: todo flow tem caminho de fallback e registra um `AIEvent`.
- **Dados do usuário**: querysets sempre filtrados por dono; valide ownership também na escrita (FKs vindas do cliente).
- **Segredos** só por variável de ambiente (`.env`, nunca versionado).
- Todo código novo vem com teste.

## Commits

Mensagens curtas em inglês, no formato `tipo(escopo): descrição` (`feat`, `fix`, `test`, `chore`, `ci`, `docs`). Um commit por mudança lógica.
