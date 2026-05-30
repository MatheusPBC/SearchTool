import os
from pathlib import Path

from fastapi.testclient import TestClient

test_db = Path("C:/tmp/research-agent-api-test.db")
test_db.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{test_db}"
os.environ["LLM_PROVIDER"] = "heuristic"

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_project() -> None:
    response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um sistema de mercado para Path of Exile",
            "target_confidence": 85,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["idea"] == "Quero criar um sistema de mercado para Path of Exile"
    assert body["can_finalize"] is False
    assert body["critical_questions"]
    assert body["mvp"]["backlog"]


def test_project_is_persisted_and_can_be_retrieved() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um agente pesquisador para descobrir MVPs",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    list_response = client.get("/projects")
    assert list_response.status_code == 200
    assert any(project["project_id"] == project_id for project in list_response.json())

    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["project_id"] == project_id


def test_project_question_can_be_marked_answered() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um sistema de pesquisa profunda para SaaS",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    questions_response = client.get(f"/projects/{project_id}/questions")
    question_id = questions_response.json()[0]["id"]

    patch_response = client.patch(
        f"/projects/{project_id}/questions/{question_id}",
        json={"answered": True},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["answered"] is True


def test_hypothesis_evidence_can_be_updated() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um agente para aprender dominios tecnicos",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    hypotheses_response = client.get(f"/projects/{project_id}/hypotheses")
    hypothesis_id = hypotheses_response.json()[0]["id"]

    patch_response = client.patch(
        f"/projects/{project_id}/hypotheses/{hypothesis_id}",
        json={"evidence_level": "strong", "confidence_score": 90},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["evidence_level"] == "strong"
    assert patch_response.json()["confidence_score"] == 90


def test_sources_and_findings_can_be_added_to_project() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um sistema de pesquisa para dominios regulados",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    source_response = client.post(
        f"/projects/{project_id}/sources",
        json={
            "title": "Documentacao oficial da API",
            "url": "https://example.com/docs",
            "source_type": "documentation",
            "reliability_score": 95,
            "notes": "Fonte primaria para limites e termos de uso.",
        },
    )
    assert source_response.status_code == 200
    assert source_response.json()["title"] == "Documentacao oficial da API"

    finding_response = client.post(
        f"/projects/{project_id}/findings",
        json={
            "statement": "A API oficial define limites que impactam o crawler do MVP.",
            "evidence_level": "strong",
            "source_titles": ["Documentacao oficial da API"],
            "confidence_score": 92,
        },
    )
    assert finding_response.status_code == 200
    assert finding_response.json()["source_titles"] == ["Documentacao oficial da API"]

    report_response = client.get(f"/projects/{project_id}")
    body = report_response.json()
    assert any(source["title"] == "Documentacao oficial da API" for source in body["sources"])
    assert any("limites" in finding["statement"] for finding in body["findings"])


def test_source_can_be_ingested_into_findings() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um agente que transforma documentacao em decisoes de MVP",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    ingest_response = client.post(
        f"/projects/{project_id}/ingest-source",
        json={
            "title": "Documentacao de limites da API",
            "url": "https://example.com/api-limits",
            "source_type": "documentation",
            "reliability_score": 90,
            "notes": "Fonte usada para extrair restricoes tecnicas.",
            "content": (
                "A API permite 120 requisicoes por minuto por token. "
                "Clientes devem implementar backoff exponencial quando receberem status 429. "
                "Dados historicos ficam disponiveis por 30 dias."
            ),
            "max_findings": 3,
        },
    )

    assert ingest_response.status_code == 200
    body = ingest_response.json()
    assert body["source"]["title"] == "Documentacao de limites da API"
    assert body["findings"]
    assert body["extraction_notes"]


def test_research_run_tracks_questions_and_generated_artifacts() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um agente que pesquisa concorrentes automaticamente",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]
    questions = client.get(f"/projects/{project_id}/questions").json()

    run_response = client.post(
        f"/projects/{project_id}/runs",
        json={
            "objective": "Pesquisar fontes oficiais e concorrentes principais",
            "question_ids": [questions[0]["id"]],
        },
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["status"] == "planned"
    assert run["planned_questions"] == [questions[0]["question"]]

    running_response = client.patch(
        f"/projects/{project_id}/runs/{run['id']}",
        json={"status": "running", "notes": "Rodada iniciada."},
    )
    assert running_response.status_code == 200
    assert running_response.json()["status"] == "running"

    source_response = client.post(
        f"/projects/{project_id}/sources",
        json={
            "title": "Repositorio de concorrente",
            "url": "https://example.com/repo",
            "source_type": "github",
            "reliability_score": 80,
            "notes": "Implementacao existente para comparar escopo.",
        },
    )
    finding_response = client.post(
        f"/projects/{project_id}/findings",
        json={
            "statement": "Concorrentes focam coleta, mas nao explicam incerteza.",
            "evidence_level": "moderate",
            "source_titles": ["Repositorio de concorrente"],
            "confidence_score": 78,
        },
    )

    runs_response = client.get(f"/projects/{project_id}/runs")
    active_run = runs_response.json()[0]

    assert source_response.json()["id"] in active_run["generated_source_ids"]
    assert finding_response.json()["id"] in active_run["generated_finding_ids"]


def test_plan_next_run_prioritizes_open_questions_and_blockers() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar um sistema que descobre MVPs em dominios desconhecidos",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    plan_response = client.post(f"/projects/{project_id}/plan-next-run")

    assert plan_response.status_code == 200
    body = plan_response.json()
    assert body["run"]["status"] == "planned"
    assert body["run"]["planned_questions"]
    assert body["targeted_blockers"]
    assert "pergunta" in body["rationale"].lower()


def test_recalculate_project_returns_current_blockers() -> None:
    create_response = client.post(
        "/projects",
        json={
            "idea": "Quero criar uma IA pesquisadora para MVPs complexos",
            "target_confidence": 85,
        },
    )
    project_id = create_response.json()["project_id"]

    recalculate_response = client.post(f"/projects/{project_id}/recalculate")

    assert recalculate_response.status_code == 200
    body = recalculate_response.json()
    assert body["project_id"] == project_id
    assert "existem perguntas criticas sem resposta" in body["blockers"]
