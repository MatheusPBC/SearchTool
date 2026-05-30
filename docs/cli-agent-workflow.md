# CLI Agent Workflow

Este projeto e pensado para ser usado por LLMs e agentes via CLI, nao apenas por humanos.

A interface principal e JSON-first:

```powershell
python -m app.cli <command>
```

Todo comando imprime JSON em stdout. Erros saem em stderr como:

```json
{"error":"Project not found"}
```

## Fluxo Minimo

Criar projeto:

```powershell
python -m app.cli create-project `
  --idea "Quero criar um sistema de mercado para Path of Exile"
```

Planejar a proxima rodada:

```powershell
python -m app.cli plan-next-run <project_id>
```

Pedir uma instrucao de proxima acao para outro agente:

```powershell
python -m app.cli next-action <project_id>
```

Marcar uma run como ativa:

```powershell
python -m app.cli update-run <project_id> <run_id> `
  --status running `
  --notes "Rodada iniciada pelo agente pesquisador."
```

Ingerir uma fonte:

```powershell
python -m app.cli ingest-source <project_id> `
  --title "Documentacao oficial da API" `
  --source-type documentation `
  --reliability-score 95 `
  --notes "Fonte primaria." `
  --content-file .\source.txt
```

Recalcular:

```powershell
python -m app.cli recalculate <project_id>
```

## Uso com Codex CLI

Um agente Codex pode operar este projeto chamando comandos shell.

Exemplo de instrucao para outro Codex:

```text
Use `python -m app.cli next-action <project_id>` para descobrir a proxima rodada.
Pesquise as perguntas planejadas, salve fontes relevantes com `ingest-source`,
marque perguntas respondidas com `answer-question` e rode `recalculate`.
Nao finalize enquanto `can_finalize=false`.
```

## Provider LLM Interno

Quando `LLM_PROVIDER=codex_cli`, os comandos que planejam ou extraem conhecimento podem chamar `codex exec` por baixo dos panos, usando o OAuth local do usuario.

```text
LLM_PROVIDER=codex_cli
CODEX_CLI_COMMAND=codex
CODEX_CLI_TIMEOUT_SECONDS=120
```

