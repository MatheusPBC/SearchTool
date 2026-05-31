from dataclasses import asdict

from app.domain.deep_research import evaluate_research_coverage
from app.domain.schemas import OpenQuestionRecord, PlannedResearchRun, ProjectReport


def build_workflow_step(
    report: ProjectReport,
    open_questions: list[OpenQuestionRecord],
    planned: PlannedResearchRun | None,
) -> dict:
    coverage = evaluate_research_coverage(
        idea=report.idea,
        sources=report.sources,
        findings=report.findings,
    )
    stage = _stage_for(report, open_questions)
    missing_facet_names = [facet.name for facet in coverage.missing_facets]

    return {
        "project_id": str(report.project_id),
        "status": "finalizable" if report.can_finalize else "needs_research",
        "current_stage": stage,
        "confidence_score": report.confidence_score,
        "target_confidence": report.target_confidence,
        "can_finalize": report.can_finalize,
        "blockers": report.blockers,
        "coverage": {
            "required_facets": [asdict(facet) for facet in coverage.required_facets],
            "covered_facets": coverage.covered_facets,
            "missing_facets": [asdict(facet) for facet in coverage.missing_facets],
            "concrete_source_count": coverage.concrete_source_count,
            "source_type_count": coverage.source_type_count,
            "competitor_source_count": coverage.competitor_source_count,
            "github_source_count": coverage.github_source_count,
        },
        "recommended_next_run": planned.model_dump(mode="json") if planned else None,
        "source_discovery_plan": _source_discovery_plan(report.idea, coverage.missing_facets),
        "expected_artifacts": _expected_artifacts(stage, missing_facet_names),
        "tool_sequence": _tool_sequence(report.can_finalize),
    }


def _stage_for(report: ProjectReport, open_questions: list[OpenQuestionRecord]) -> str:
    if report.can_finalize:
        return "finalize_mvp"
    if open_questions:
        return "answer_critical_questions"
    if any("faceta critica" in blocker.lower() for blocker in report.blockers):
        return "cover_missing_domain_facets"
    if any("fontes concretas" in blocker.lower() for blocker in report.blockers):
        return "expand_source_breadth"
    if any("repositorio" in blocker.lower() or "github" in blocker.lower() for blocker in report.blockers):
        return "inspect_open_implementations"
    if any("hipoteses" in blocker.lower() for blocker in report.blockers):
        return "validate_or_refute_hypotheses"
    return "deepen_evidence"


def _source_discovery_plan(idea: str, missing_facets) -> list[dict]:
    facets = list(missing_facets)
    if not facets:
        facets = []

    plans = [
        {
            "facet": facet.name,
            "why": facet.description,
            "queries": [
                f"{idea} {facet.description} official documentation",
                f"{idea} {' '.join(facet.keywords[:4])} GitHub repository implementation",
                f"{idea} {' '.join(facet.keywords[:4])} competitor alternative",
                f"{idea} {' '.join(facet.keywords[:4])} forum discussion user workflow",
            ],
            "source_types_to_collect": [
                "official_documentation",
                "github_repository",
                "competitor_documentation",
                "community_discussion",
            ],
        }
        for facet in facets
    ]

    if plans:
        return plans

    return [
        {
            "facet": "source_breadth",
            "why": "A pesquisa precisa de mais diversidade antes de finalizar.",
            "queries": [
                f"{idea} official documentation",
                f"{idea} GitHub repository implementation",
                f"{idea} competitor platform alternative",
                f"{idea} community forum workflow pain points",
            ],
            "source_types_to_collect": [
                "official_documentation",
                "github_repository",
                "competitor_documentation",
                "community_discussion",
            ],
        }
    ]


def _expected_artifacts(stage: str, missing_facet_names: list[str]) -> list[str]:
    base = [
        "persistir pelo menos 2 fontes novas com URL por faceta pesquisada",
        "criar findings com source_titles apontando para fontes reais",
        "marcar perguntas criticas como respondidas somente quando houver evidencia",
        "atualizar hipoteses fracas apenas quando houver suporte ou refutacao",
        "recalcular e repetir o workflow",
    ]
    if missing_facet_names:
        return [
            f"cobrir facetas faltantes: {', '.join(missing_facet_names)}",
            *base,
        ]
    if stage == "finalize_mvp":
        return ["gerar MVP, arquitetura, riscos e backlog final com rastreabilidade"]
    return base


def _tool_sequence(can_finalize: bool) -> list[str]:
    if can_finalize:
        return ["show_project", "final_answer"]

    return [
        "advance_workflow",
        "buscar fontes externas relevantes",
        "ingest_source ou create_finding para cada evidencia util",
        "answer_question quando uma pergunta critica estiver sustentada",
        "update_hypothesis quando uma hipotese for sustentada ou refutada",
        "recalculate",
        "advance_workflow novamente",
    ]
