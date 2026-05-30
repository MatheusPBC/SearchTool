# Autonomous Research-to-MVP Agent

Sistema de IA para transformar uma ideia vaga em pesquisa de dominio, conhecimento persistente e um MVP recomendado.

Este projeto nao e um chatbot. O objetivo e construir um agente pesquisador que:

- descobre perguntas criticas sozinho;
- pesquisa fontes e concorrentes;
- separa fatos, hipoteses, decisoes e lacunas;
- constroi um mapa de dominio;
- critica conclusoes antes de propor um MVP;
- so considera o trabalho pronto quando a confianca atinge o limite definido.

## MVP V1

Entrada:

```text
Quero construir um sistema de mercado para Path of Exile
```

Saida:

1. mapa do dominio;
2. perguntas criticas;
3. fontes relevantes;
4. concorrentes;
5. hipoteses;
6. riscos;
7. arquitetura sugerida;
8. MVP recomendado;
9. backlog inicial.

## Stack Planejada

- Backend: Python + FastAPI
- Banco: PostgreSQL
- Vetorial: pgvector
- Jobs: Redis + Celery
- Busca: web search, GitHub search e crawlers
- LLM: modelo de raciocinio configuravel

## Rodando Localmente

Crie um ambiente Python e instale as dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copie o arquivo de ambiente:

```powershell
Copy-Item .env.example .env
```

Por padrao o projeto usa SQLite local para desenvolvimento rapido:

```text
DATABASE_URL=sqlite:///./research_mvp.db
```

Para usar PostgreSQL do `docker-compose.yml`:

```text
DATABASE_URL=postgresql+psycopg://research:research@localhost:5432/research_mvp
```

Para usar o Codex CLI como provider de planejamento:

```text
LLM_PROVIDER=codex_cli
CODEX_CLI_COMMAND=codex
CODEX_CLI_MODEL=
CODEX_CLI_TIMEOUT_SECONDS=120
```

Suba a API:

```powershell
uvicorn app.main:app --reload
```

Teste:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/projects `
  -ContentType "application/json" `
  -Body '{"idea":"Quero criar um sistema de mercado para Path of Exile","target_confidence":85}'
```

## Endpoints Iniciais

- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/questions`
- `PATCH /projects/{project_id}/questions/{question_id}`
- `GET /projects/{project_id}/sources`
- `POST /projects/{project_id}/sources`
- `POST /projects/{project_id}/ingest-source`
- `GET /projects/{project_id}/runs`
- `POST /projects/{project_id}/runs`
- `PATCH /projects/{project_id}/runs/{run_id}`
- `POST /projects/{project_id}/plan-next-run`
- `GET /projects/{project_id}/findings`
- `POST /projects/{project_id}/findings`
- `GET /projects/{project_id}/hypotheses`
- `PATCH /projects/{project_id}/hypotheses/{hypothesis_id}`
- `POST /projects/{project_id}/recalculate`

## Primeiro Ciclo Operacional

1. Crie um projeto com `POST /projects`.
2. Liste perguntas criticas com `GET /projects/{project_id}/questions`.
3. Crie uma rodada manualmente com `POST /projects/{project_id}/runs` ou gere a proxima automaticamente com `POST /projects/{project_id}/plan-next-run`.
4. Marque a rodada como `running` com `PATCH /projects/{project_id}/runs/{run_id}`.
5. Registre fontes com `POST /projects/{project_id}/sources` ou envie conteudo para extracao com `POST /projects/{project_id}/ingest-source`.
6. Registre fatos extraidos manualmente com `POST /projects/{project_id}/findings` quando necessario.
7. Marque perguntas respondidas com `PATCH /projects/{project_id}/questions/{question_id}`.
8. Liste hipoteses com `GET /projects/{project_id}/hypotheses`.
9. Atualize evidencia e confianca com `PATCH /projects/{project_id}/hypotheses/{hypothesis_id}`.
10. Recalcule o estado com `POST /projects/{project_id}/recalculate`.
11. Feche a rodada como `completed` ou `blocked`.

O projeto so retorna `can_finalize=true` quando nao existem blockers e a confianca atinge o alvo.

## Usando Codex CLI como LLM

O projeto pode usar o Codex CLI como provider de planejamento, aproveitando o login/OAuth local do usuario.

Quando `LLM_PROVIDER=codex_cli`, `POST /projects/{project_id}/plan-next-run` chama `codex exec` em modo nao interativo com schema de saida JSON. Se o CLI falhar, expirar ou retornar JSON invalido, o sistema usa o planner heuristico como fallback.

O mesmo provider tambem e usado por `POST /projects/{project_id}/ingest-source` para extrair findings do conteudo fornecido. O extractor e instruido a nao inventar fatos fora da fonte.

## Estrutura

```text
app/
  agents/       agentes internos do loop de pesquisa
  domain/       entidades, schemas, persistencia e regras de confianca
  cli.py        interface JSON-first para LLMs e agentes
  main.py       API FastAPI
docs/
  architecture.md
  cli-agent-workflow.md
  mcp-codex-setup.md
  product-spec.md
```

## CLI Para Agentes

A interface recomendada para uso via Codex/LLMs e:

```powershell
python -m app.cli <command>
```

Veja [docs/cli-agent-workflow.md](docs/cli-agent-workflow.md).

## MCP Para Codex

O servidor MCP roda com:

```powershell
python -m app.mcp_server
```

Veja [docs/mcp-codex-setup.md](docs/mcp-codex-setup.md).
