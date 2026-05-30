from app.domain.schemas import Decision, MvpPlan


class MvpBuilder:
    def build_plan(self) -> MvpPlan:
        return MvpPlan(
            recommended_mvp=(
                "Um workspace de pesquisa que recebe uma ideia, cria perguntas criticas, "
                "registra fontes, extrai findings, cria hipoteses criticaveis e gera um "
                "plano de MVP com confidence score."
            ),
            architecture=[
                "FastAPI para API e orquestracao inicial.",
                "PostgreSQL para projetos, fontes, findings, hipoteses, perguntas e decisoes.",
                "pgvector para recuperar fontes e findings semanticamente similares.",
                "Redis e Celery para pesquisas longas e reprocessamento assincromo.",
                "Adaptadores de busca separados para web, GitHub e crawlers de documentacao.",
            ],
            backlog=[
                "Criar CRUD persistente de Project, Source, Finding, Hypothesis e OpenQuestion.",
                "Implementar scoring de confianca com rastreabilidade por evidencia.",
                "Adicionar busca web e GitHub como SourceFinder real.",
                "Criar tela de mapa de dominio com entidades e relacoes.",
                "Adicionar fluxo de critica: aprovar, refutar ou pedir mais pesquisa por hipotese.",
                "Gerar backlog e arquitetura em formato exportavel.",
            ],
            risks=[
                "Fontes comunitarias podem ter vies alto.",
                "Busca automatica pode coletar dados irrelevantes sem bom ranking.",
                "Confidence score pode parecer preciso demais se nao for auditavel.",
                "Crawlers podem violar termos de uso se nao houver verificacao por fonte.",
            ],
        )

    def make_decisions(self) -> list[Decision]:
        return [
            Decision(
                decision="Comecar por persistencia estruturada antes de automacao total de pesquisa.",
                rationale="Sem fatos, fontes e hipoteses como entidades, o produto vira apenas chat com historico.",
                confidence_score=82,
            ),
            Decision(
                decision="Representar grafo primeiro em PostgreSQL antes de adicionar banco de grafo dedicado.",
                rationale="Reduz complexidade operacional enquanto valida se consultas de grafo sao centrais.",
                confidence_score=76,
            ),
        ]

