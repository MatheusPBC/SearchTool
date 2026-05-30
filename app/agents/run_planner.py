import json
from dataclasses import dataclass

from app.config import settings
from app.domain.schemas import EvidenceLevel, Hypothesis, OpenQuestionRecord, ProjectReport
from app.llm.codex_cli import CodexCliClient, CodexCliError


@dataclass(frozen=True)
class RunPlan:
    objective: str
    question_ids: list[int]
    rationale: str
    targeted_blockers: list[str]


class RunPlanner:
    def __init__(self, codex_client: CodexCliClient | None = None) -> None:
        self.codex_client = codex_client or CodexCliClient()

    def plan_next_run(
        self,
        report: ProjectReport,
        open_questions: list[OpenQuestionRecord],
    ) -> RunPlan:
        if settings.llm_provider == "codex_cli":
            try:
                return self._plan_with_codex_cli(report, open_questions)
            except CodexCliError:
                return self._plan_with_heuristics(report, open_questions)

        return self._plan_with_heuristics(report, open_questions)

    def _plan_with_codex_cli(
        self,
        report: ProjectReport,
        open_questions: list[OpenQuestionRecord],
    ) -> RunPlan:
        response = self.codex_client.complete_json(
            prompt=_build_prompt(report, open_questions),
            output_schema=_run_plan_schema(),
        )

        available_question_ids = {question.id for question in open_questions}
        selected_question_ids = [
            question_id
            for question_id in response.get("question_ids", [])
            if isinstance(question_id, int) and question_id in available_question_ids
        ][:3]

        objective = str(response.get("objective", "")).strip()
        rationale = str(response.get("rationale", "")).strip()
        targeted_blockers = [
            str(blocker)
            for blocker in response.get("targeted_blockers", [])
            if isinstance(blocker, str)
        ]

        if len(objective) < 10 or not selected_question_ids and open_questions:
            return self._plan_with_heuristics(report, open_questions)

        return RunPlan(
            objective=objective,
            question_ids=selected_question_ids,
            rationale=rationale or "Planejado pelo Codex CLI a partir do estado persistido.",
            targeted_blockers=targeted_blockers or report.blockers,
        )

    def _plan_with_heuristics(
        self,
        report: ProjectReport,
        open_questions: list[OpenQuestionRecord],
    ) -> RunPlan:
        selected_questions = sorted(
            open_questions,
            key=lambda question: (-question.criticality, question.id),
        )[:3]
        weak_hypotheses = _weak_hypotheses(report.hypotheses)

        objective_parts: list[str] = []
        if selected_questions:
            objective_parts.append("Responder perguntas criticas abertas")
        if weak_hypotheses:
            objective_parts.append("Buscar evidencia para hipoteses fracas")
        if any("concorrente" in blocker.lower() for blocker in report.blockers):
            objective_parts.append("Analisar concorrentes relevantes")
        if not objective_parts:
            objective_parts.append("Revisar evidencias e confirmar criterios de finalizacao")

        rationale_parts = ["A rodada foi planejada a partir do estado persistido do projeto."]
        if selected_questions:
            rationale_parts.append(
                f"{len(selected_questions)} pergunta(s) aberta(s) de maior criticidade foram priorizadas."
            )
        if weak_hypotheses:
            rationale_parts.append(
                f"{len(weak_hypotheses)} hipotese(s) ainda precisam de evidencia melhor."
            )
        if report.blockers:
            rationale_parts.append("Blockers atuais impedem finalizacao do projeto.")

        return RunPlan(
            objective="; ".join(objective_parts),
            question_ids=[question.id for question in selected_questions],
            rationale=" ".join(rationale_parts),
            targeted_blockers=report.blockers,
        )


def _weak_hypotheses(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    return [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.evidence_level in {EvidenceLevel.none, EvidenceLevel.weak}
    ]


def _build_prompt(report: ProjectReport, open_questions: list[OpenQuestionRecord]) -> str:
    payload = {
        "project": {
            "idea": report.idea,
            "confidence_score": report.confidence_score,
            "target_confidence": report.target_confidence,
            "blockers": report.blockers,
        },
        "open_questions": [
            {
                "id": question.id,
                "question": question.question,
                "criticality": question.criticality,
                "impact_on_mvp": question.impact_on_mvp,
            }
            for question in open_questions
        ],
        "hypotheses": [
            {
                "statement": hypothesis.statement,
                "evidence_level": hypothesis.evidence_level.value,
                "confidence_score": hypothesis.confidence_score,
            }
            for hypothesis in report.hypotheses
        ],
    }

    return (
        "Voce e o Research Planner de um agente autonomo de pesquisa para MVPs.\n"
        "Escolha a proxima rodada de pesquisa com base no estado abaixo.\n"
        "Priorize perguntas criticas abertas, hipoteses fracas e blockers que impedem finalizacao.\n"
        "Nao invente IDs de perguntas: use apenas IDs presentes em open_questions.\n"
        "Retorne somente JSON valido no schema solicitado.\n\n"
        f"STATE:\n{json.dumps(payload, ensure_ascii=True, indent=2)}"
    )


def _run_plan_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "objective": {"type": "string"},
            "question_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "maxItems": 3,
            },
            "rationale": {"type": "string"},
            "targeted_blockers": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["objective", "question_ids", "rationale", "targeted_blockers"],
    }

