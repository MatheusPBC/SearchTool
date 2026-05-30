from app.domain.schemas import OpenQuestion


class ResearchPlanner:
    def generate_questions(self, idea: str) -> list[OpenQuestion]:
        return [
            OpenQuestion(
                question=f"Quais usuarios sentem dor suficiente para pagar por: {idea}?",
                criticality=5,
                impact_on_mvp="Define ICP, posicionamento e escopo inicial.",
            ),
            OpenQuestion(
                question="Quais fontes de dados sao oficiais, confiaveis e legalmente utilizaveis?",
                criticality=5,
                impact_on_mvp="Define viabilidade tecnica e risco juridico.",
            ),
            OpenQuestion(
                question="Quais concorrentes resolvem partes do problema hoje?",
                criticality=4,
                impact_on_mvp="Evita construir uma copia pior de ferramentas existentes.",
            ),
            OpenQuestion(
                question="Quais metricas indicam que o MVP realmente aprendeu o dominio?",
                criticality=4,
                impact_on_mvp="Define criterio de sucesso alem de uma demo superficial.",
            ),
            OpenQuestion(
                question="Quais dependencias tecnicas podem bloquear coleta, ranking ou avaliacao de confianca?",
                criticality=5,
                impact_on_mvp="Define arquitetura e plano de mitigacao.",
            ),
        ]

