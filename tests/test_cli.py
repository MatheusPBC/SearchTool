import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def test_cli_project_flow() -> None:
    tmp_path = Path(f"research-agent-cli-test-{uuid4()}")
    tmp_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{(tmp_path / 'cli.db').as_posix()}"
    env["LLM_PROVIDER"] = "heuristic"

    create = _run_cli(
        [
            "create-project",
            "--idea",
            "Quero criar uma ferramenta de pesquisa para LLMs colaborarem",
        ],
        env,
    )
    project_id = create["project_id"]
    assert create["can_finalize"] is False

    planned = _run_cli(["plan-next-run", project_id], env)
    assert planned["run"]["status"] == "planned"
    assert planned["run"]["planned_questions"]

    next_action = _run_cli(["next-action", project_id], env)
    assert next_action["recommended_next_run"]
    assert next_action["suggested_agent_instruction"]

    ingested = _run_cli(
        [
            "ingest-source",
            project_id,
            "--title",
            "Documento de arquitetura",
            "--source-type",
            "documentation",
            "--reliability-score",
            "80",
            "--notes",
            "Fonte usada para validar arquitetura.",
            "--content",
            (
                "O sistema deve expor uma CLI JSON-first para que LLMs possam criar projetos, "
                "planejar rodadas, ingerir fontes e recalcular confianca de forma auditavel."
            ),
        ],
        env,
    )
    assert ingested["source"]["title"] == "Documento de arquitetura"
    assert ingested["findings"] == []

    finding = _run_cli(
        [
            "create-finding",
            project_id,
            "--statement",
            "Finding temporario para testar delecao.",
            "--evidence-level",
            "weak",
            "--confidence-score",
            "30",
        ],
        env,
    )
    deleted = _run_cli(["delete-finding", project_id, str(finding["id"])], env)
    assert deleted["deleted"] is True


def _run_cli(args: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
