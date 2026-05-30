from app.domain.schemas import Finding, Hypothesis, OpenQuestion, Source


def calculate_confidence(
    sources: list[Source],
    findings: list[Finding],
    hypotheses: list[Hypothesis],
    questions: list[OpenQuestion],
) -> int:
    if not findings and not hypotheses:
        return 0

    source_score = sum(source.reliability_score for source in sources) / max(len(sources), 1)
    finding_score = sum(finding.confidence_score for finding in findings) / max(len(findings), 1)
    hypothesis_score = sum(h.confidence_score for h in hypotheses) / max(len(hypotheses), 1)

    unanswered_penalty = sum(question.criticality * 4 for question in questions if not question.answered)
    unsupported_penalty = sum(15 for h in hypotheses if h.evidence_level in {"none", "weak"})

    score = (source_score * 0.25) + (finding_score * 0.4) + (hypothesis_score * 0.35)
    score -= unanswered_penalty + unsupported_penalty

    return max(0, min(100, round(score)))


def find_completion_blockers(
    target_confidence: int,
    confidence_score: int,
    questions: list[OpenQuestion],
    hypotheses: list[Hypothesis],
    competitors: list[str],
) -> list[str]:
    blockers: list[str] = []

    if confidence_score < target_confidence:
        blockers.append(f"confidence_score atual {confidence_score} abaixo do alvo {target_confidence}")

    if any(question.criticality >= 4 and not question.answered for question in questions):
        blockers.append("existem perguntas criticas sem resposta")

    if any(h.evidence_level in {"none", "weak"} for h in hypotheses):
        blockers.append("existem hipoteses sem evidencia suficiente")

    if not competitors:
        blockers.append("nenhum concorrente relevante analisado")

    return blockers

