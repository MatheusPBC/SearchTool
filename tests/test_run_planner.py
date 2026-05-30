from app.agents.run_planner import RunPlanner
from app.config import settings
from app.domain.schemas import (
    EvidenceLevel,
    Hypothesis,
    MvpPlan,
    OpenQuestionRecord,
    ProjectReport,
)


class FakeCodexClient:
    def complete_json(self, prompt: str, output_schema: dict) -> dict:
        assert "STATE:" in prompt
        assert output_schema["type"] == "object"
        return {
            "objective": "Validar API oficial e concorrentes diretos",
            "question_ids": [10],
            "rationale": "A pergunta mais critica depende de fonte oficial.",
            "targeted_blockers": ["existem perguntas criticas sem resposta"],
        }


def test_run_planner_uses_heuristic_by_default() -> None:
    previous_provider = settings.llm_provider
    settings.llm_provider = "heuristic"
    try:
        plan = RunPlanner().plan_next_run(_report(), _questions())
    finally:
        settings.llm_provider = previous_provider

    assert plan.question_ids == [10, 11]
    assert "perguntas criticas" in plan.objective.lower()
    assert plan.targeted_blockers


def test_run_planner_can_use_codex_cli_client() -> None:
    previous_provider = settings.llm_provider
    settings.llm_provider = "codex_cli"
    try:
        plan = RunPlanner(codex_client=FakeCodexClient()).plan_next_run(_report(), _questions())
    finally:
        settings.llm_provider = previous_provider

    assert plan.objective == "Validar API oficial e concorrentes diretos"
    assert plan.question_ids == [10]
    assert plan.rationale == "A pergunta mais critica depende de fonte oficial."


def _questions() -> list[OpenQuestionRecord]:
    return [
        OpenQuestionRecord(
            id=10,
            question="Quais APIs oficiais existem?",
            criticality=5,
            impact_on_mvp="Define viabilidade tecnica.",
        ),
        OpenQuestionRecord(
            id=11,
            question="Quais concorrentes precisam ser analisados?",
            criticality=4,
            impact_on_mvp="Define diferenciacao.",
        ),
    ]


def _report() -> ProjectReport:
    return ProjectReport(
        idea="Quero criar um sistema de mercado para Path of Exile",
        confidence_score=40,
        target_confidence=85,
        can_finalize=False,
        domain_map=[],
        critical_questions=[],
        sources=[],
        competitors=[],
        findings=[],
        hypotheses=[
            Hypothesis(
                statement="O MVP pode comecar com fontes oficiais.",
                evidence_level=EvidenceLevel.weak,
                confidence_score=50,
            )
        ],
        decisions=[],
        mvp=MvpPlan(recommended_mvp="", architecture=[], backlog=[], risks=[]),
        blockers=["existem perguntas criticas sem resposta"],
    )

