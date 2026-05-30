from app.domain.schemas import EvidenceLevel, Hypothesis, OpenQuestion


class Critic:
    def create_hypotheses(self) -> list[Hypothesis]:
        return [
            Hypothesis(
                statement="O diferencial do produto sera a gestao explicita de incerteza, nao a interface conversacional.",
                evidence_level=EvidenceLevel.moderate,
                confidence_score=70,
                falsification_questions=[
                    "Usuarios aceitariam um fluxo menos conversacional em troca de rastreabilidade?",
                    "Concorrentes ja oferecem confidence scoring auditavel?",
                ],
            ),
            Hypothesis(
                statement="Um MVP util pode comecar com pesquisa semiautomatica e persistencia estruturada antes de crawlers completos.",
                evidence_level=EvidenceLevel.weak,
                confidence_score=58,
                falsification_questions=[
                    "A coleta manual assistida e suficiente para gerar valor?",
                    "Sem busca automatica, o agente ainda descobre lacunas relevantes?",
                ],
            ),
        ]

    def find_gaps(self, questions: list[OpenQuestion], hypotheses: list[Hypothesis]) -> list[str]:
        gaps = [q.question for q in questions if q.criticality >= 4 and not q.answered]
        gaps.extend(h.statement for h in hypotheses if h.evidence_level in {EvidenceLevel.none, EvidenceLevel.weak})
        return gaps

