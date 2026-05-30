from app.domain.schemas import DomainEntity, EvidenceLevel, Finding, Relationship, Source


class KnowledgeExtractor:
    def extract_findings(self, idea: str, sources: list[Source]) -> list[Finding]:
        source_titles = [source.title for source in sources]

        return [
            Finding(
                statement="O produto precisa separar fatos verificados, hipoteses e lacunas para nao virar historico de conversa.",
                evidence_level=EvidenceLevel.moderate,
                source_titles=source_titles,
                confidence_score=72,
            ),
            Finding(
                statement="A primeira versao deve priorizar rastreabilidade entre conclusao, fonte e impacto no MVP.",
                evidence_level=EvidenceLevel.moderate,
                source_titles=source_titles,
                confidence_score=74,
            ),
            Finding(
                statement=f"A ideia inicial ainda esta vaga e precisa ser decomposta em topicos pesquisaveis: {idea}.",
                evidence_level=EvidenceLevel.strong,
                source_titles=[],
                confidence_score=88,
            ),
        ]

    def extract_entities(self) -> list[DomainEntity]:
        return [
            DomainEntity(name="Ideia", entity_type="input", description="Pedido inicial do usuario."),
            DomainEntity(name="Pergunta critica", entity_type="research_object", description="Lacuna que pode mudar o MVP."),
            DomainEntity(name="Fonte", entity_type="evidence", description="Origem usada para sustentar fatos e hipoteses."),
            DomainEntity(name="Hipotese", entity_type="claim", description="Conclusao provisoria sujeita a critica."),
            DomainEntity(name="MVP", entity_type="output", description="Produto minimo recomendado a partir do conhecimento acumulado."),
        ]

    def extract_relationships(self) -> list[Relationship]:
        return [
            Relationship(source="Ideia", target="Pergunta critica", relation="gera", confidence_score=85),
            Relationship(source="Pergunta critica", target="Fonte", relation="orienta_busca_por", confidence_score=80),
            Relationship(source="Fonte", target="Hipotese", relation="sustenta_ou_refuta", confidence_score=75),
            Relationship(source="Hipotese", target="MVP", relation="altera_escopo_de", confidence_score=72),
        ]

