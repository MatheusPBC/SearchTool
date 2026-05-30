# MCP Setup for Codex CLI

Este projeto pode rodar como MCP server stdio.

## Comando

```powershell
C:\Users\mathe\Documents\vscode\saas\autonomous-research-mvp\.venv\Scripts\python.exe -m app.mcp_server
```

## Configuracao Codex

Adicione ao `~/.codex/config.toml`:

```toml
[mcp_servers.research_mvp]
command = "C:\\Users\\mathe\\Documents\\vscode\\saas\\autonomous-research-mvp\\.venv\\Scripts\\python.exe"
args = ["-m", "app.mcp_server"]
cwd = "C:\\Users\\mathe\\Documents\\vscode\\saas\\autonomous-research-mvp"
```

## Tools Disponiveis

- `create_project`
- `list_projects`
- `show_project`
- `list_questions`
- `answer_question`
- `plan_next_run`
- `next_action`
- `list_runs`
- `create_run`
- `update_run`
- `ingest_source`
- `list_findings`
- `create_finding`
- `list_hypotheses`
- `update_hypothesis`
- `recalculate`

## Uso Esperado

Um agente deve:

1. Criar ou abrir um projeto.
2. Chamar `next_action`.
3. Executar a pesquisa solicitada.
4. Chamar `ingest_source` para cada fonte relevante.
5. Marcar perguntas respondidas com `answer_question`.
6. Atualizar hipoteses com `update_hypothesis`.
7. Chamar `recalculate`.
8. Repetir ate `can_finalize=true`.

