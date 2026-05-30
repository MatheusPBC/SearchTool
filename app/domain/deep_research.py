from dataclasses import dataclass

from app.domain.schemas import Finding, Source


@dataclass(frozen=True)
class ResearchFacet:
    name: str
    keywords: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ResearchCoverage:
    required_facets: list[ResearchFacet]
    covered_facets: list[str]
    missing_facets: list[ResearchFacet]
    concrete_source_count: int
    source_type_count: int
    competitor_source_count: int
    github_source_count: int


MIN_CONCRETE_SOURCES = 10
MIN_SOURCE_TYPES = 5
MIN_COMPETITOR_SOURCES = 3


def evaluate_research_coverage(
    idea: str,
    sources: list[Source],
    findings: list[Finding],
) -> ResearchCoverage:
    required_facets = required_facets_for_idea(idea)
    searchable_text = _searchable_text(sources, findings)
    covered_facets = [
        facet.name
        for facet in required_facets
        if any(keyword in searchable_text for keyword in facet.keywords)
    ]
    covered_names = set(covered_facets)

    concrete_sources = [source for source in sources if source.url]
    source_types = {source.source_type for source in concrete_sources}
    competitor_sources = [
        source
        for source in concrete_sources
        if any(token in source.source_type.lower() for token in ("competitor", "platform", "github"))
    ]
    github_sources = [
        source
        for source in concrete_sources
        if "github" in source.source_type.lower()
        or "github.com" in (source.url or "").lower()
        or "repo" in source.source_type.lower()
    ]

    return ResearchCoverage(
        required_facets=required_facets,
        covered_facets=covered_facets,
        missing_facets=[facet for facet in required_facets if facet.name not in covered_names],
        concrete_source_count=len(concrete_sources),
        source_type_count=len(source_types),
        competitor_source_count=len(competitor_sources),
        github_source_count=len(github_sources),
    )


def required_facets_for_idea(idea: str) -> list[ResearchFacet]:
    # These facets are intentionally domain-agnostic. They force the agent to ask
    # "what kind of thing is this domain made of?" instead of relying on templates
    # for specific domains such as games, security, finance, or devtools.
    return [
        ResearchFacet(
            "primary_authoritative_sources",
            (
                "official",
                "documentation",
                "docs",
                "api",
                "standard",
                "specification",
                "policy",
                "terms",
            ),
            "Fontes primarias, documentacao oficial, normas, politicas e limites de uso.",
        ),
        ResearchFacet(
            "domain_object_taxonomy",
            (
                "taxonomy",
                "type",
                "class",
                "category",
                "attribute",
                "property",
                "modifier",
                "weight",
                "item",
                "asset",
                "entity",
                "skill",
                "competency",
            ),
            "Quais objetos existem no dominio, quais atributos os diferenciam e quais mudam valor/risco.",
        ),
        ResearchFacet(
            "causal_and_temporal_dynamics",
            (
                "trend",
                "change",
                "patch",
                "release",
                "season",
                "cycle",
                "meta",
                "demand",
                "supply",
                "feedback loop",
                "causal",
            ),
            "O que muda ao longo do tempo e quais relacoes de causa e efeito alteram o MVP.",
        ),
        ResearchFacet(
            "user_workflows_and_jobs",
            (
                "workflow",
                "pain",
                "user",
                "persona",
                "job",
                "journey",
                "process",
                "manual",
                "workaround",
            ),
            "Fluxos reais, dores, usuarios, jobs-to-be-done e workarounds atuais.",
        ),
        ResearchFacet(
            "data_surfaces_and_integrations",
            (
                "data",
                "dataset",
                "api",
                "integration",
                "crawler",
                "source",
                "schema",
                "database",
                "event",
                "rate limit",
            ),
            "Dados disponiveis, schemas, integracoes, confiabilidade, custos e limites.",
        ),
        ResearchFacet(
            "existing_tools_and_competitors",
            (
                "competitor",
                "alternative",
                "platform",
                "tool",
                "product",
                "marketplace",
                "academy",
                "service",
            ),
            "Concorrentes, substitutos, produtos, plataformas e ferramentas ja usadas.",
        ),
        ResearchFacet(
            "open_implementations_and_repos",
            (
                "github",
                "repository",
                "repo",
                "open source",
                "implementation",
                "library",
                "package",
                "sdk",
            ),
            "Repositorios, bibliotecas, SDKs e implementacoes abertas que revelam conhecimento pratico.",
        ),
        ResearchFacet(
            "evaluation_metrics_and_ground_truth",
            (
                "metric",
                "score",
                "accuracy",
                "quality",
                "benchmark",
                "ground truth",
                "validation",
                "rubric",
                "success",
            ),
            "Metricas, benchmark, ground truth, rubricas e criterios de sucesso do MVP.",
        ),
        ResearchFacet(
            "risks_and_constraints",
            (
                "risk",
                "legal",
                "ethical",
                "security",
                "technical",
                "constraint",
                "limitation",
                "abuse",
                "compliance",
            ),
            "Riscos, restricoes tecnicas, legais, eticas, operacionais e vetores de abuso.",
        ),
    ]


def deep_research_blockers(coverage: ResearchCoverage) -> list[str]:
    blockers: list[str] = []

    if coverage.concrete_source_count < MIN_CONCRETE_SOURCES:
        blockers.append(
            "fontes concretas insuficientes: "
            f"{coverage.concrete_source_count}/{MIN_CONCRETE_SOURCES}"
        )

    if coverage.source_type_count < MIN_SOURCE_TYPES:
        blockers.append(
            "diversidade de tipos de fonte insuficiente: "
            f"{coverage.source_type_count}/{MIN_SOURCE_TYPES}"
        )

    if coverage.competitor_source_count < MIN_COMPETITOR_SOURCES:
        blockers.append(
            "concorrentes/repositorios relevantes insuficientes: "
            f"{coverage.competitor_source_count}/{MIN_COMPETITOR_SOURCES}"
        )

    if coverage.github_source_count == 0:
        blockers.append("nenhum repositorio GitHub ou implementacao aberta analisado")

    for facet in coverage.missing_facets:
        blockers.append(f"faceta critica sem cobertura: {facet.name} - {facet.description}")

    return blockers


def _searchable_text(sources: list[Source], findings: list[Finding]) -> str:
    source_text = " ".join(
        " ".join(
            [
                source.title,
                source.url or "",
                source.source_type,
                source.notes,
            ]
        )
        for source in sources
    )
    finding_text = " ".join(
        " ".join([finding.statement, " ".join(finding.source_titles)])
        for finding in findings
    )
    return f"{source_text} {finding_text}".lower()
