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
    normalized = idea.lower()
    if any(token in normalized for token in ("path of exile", "poe", "mercado")):
        return [
            ResearchFacet(
                "official_data_surface",
                ("api", "public stash", "currency exchange", "developer docs", "rate limit"),
                "APIs oficiais, limites, autenticacao e termos de uso.",
            ),
            ResearchFacet(
                "patch_and_league_dynamics",
                ("patch", "league", "season", "meta", "balance"),
                "Como patches, ligas e balanceamento mudam oferta, demanda e preco.",
            ),
            ResearchFacet(
                "build_meta_demand",
                ("build", "skill", "meta build", "ladder", "poe.ninja"),
                "Como builds e popularidade de skills afetam demanda por itens.",
            ),
            ResearchFacet(
                "item_model_and_weights",
                ("item weight", "mod weight", "affix", "modifier", "craft", "base type"),
                "Tipos de item, mods, pesos, crafting e diferenca entre precificar itens distintos.",
            ),
            ResearchFacet(
                "liquidity_and_manipulation",
                ("liquidity", "volume", "price fixing", "fake listing", "spread"),
                "Liquidez, manipulacao, listings falsos e preco executavel.",
            ),
            ResearchFacet(
                "competitors_and_repos",
                ("awakened", "poe.ninja", "github", "repository", "trade macro"),
                "Ferramentas, repositorios e alternativas usadas pela comunidade.",
            ),
            ResearchFacet(
                "player_workflows",
                ("bulk", "live search", "whisper", "stash", "trade"),
                "Fluxos reais de compra/venda, bulk trading e friccoes de usuario.",
            ),
        ]

    if any(token in normalized for token in ("hacker", "hacking", "cyber", "seguranca")):
        return [
            ResearchFacet(
                "legal_and_scope",
                ("authorized", "autorizacao", "scope", "disclosure", "cisa", "legal"),
                "Autorizacao, disclosure responsavel, limites legais e regras de escopo.",
            ),
            ResearchFacet(
                "skills_framework",
                ("nice", "framework", "competenc", "knowledge", "skill", "task"),
                "Competencias, conhecimentos e tarefas profissionais esperadas.",
            ),
            ResearchFacet(
                "safe_labs_and_ctfs",
                ("lab", "ctf", "sandbox", "academy", "controlled environment"),
                "Ambientes seguros de pratica e exercicios controlados.",
            ),
            ResearchFacet(
                "web_testing_methodology",
                ("owasp", "wstg", "testing guide", "web security"),
                "Metodologia defensiva de testes web.",
            ),
            ResearchFacet(
                "reporting_and_communication",
                ("report", "writeup", "reproduc", "impact", "mitigation"),
                "Qualidade de reports, reproducibilidade, impacto e mitigacao.",
            ),
            ResearchFacet(
                "competitors_and_learning_platforms",
                ("portswigger", "hack the box", "tryhackme", "hackerone", "academy"),
                "Plataformas concorrentes, trilhas, labs e modelos de progresso.",
            ),
            ResearchFacet(
                "assessment_and_progress",
                ("assessment", "rubric", "score", "badge", "progress"),
                "Diagnostico, rubricas, progresso e avaliacao por competencia.",
            ),
        ]

    return [
        ResearchFacet(
            "official_sources",
            ("official", "documentation", "api", "standard", "policy"),
            "Fontes oficiais, politicas, padroes e documentacao primaria.",
        ),
        ResearchFacet(
            "competitors",
            ("competitor", "alternative", "github", "repository", "platform"),
            "Concorrentes, alternativas e implementacoes existentes.",
        ),
        ResearchFacet(
            "user_workflows",
            ("workflow", "pain", "user", "job", "persona"),
            "Usuarios, dores, fluxos e jobs-to-be-done.",
        ),
        ResearchFacet(
            "data_and_integrations",
            ("data", "api", "integration", "crawler", "source"),
            "Dados, integracoes, disponibilidade e confiabilidade.",
        ),
        ResearchFacet(
            "evaluation_metrics",
            ("metric", "score", "accuracy", "quality", "success"),
            "Metricas de sucesso, qualidade e validacao.",
        ),
        ResearchFacet(
            "risks_and_constraints",
            ("risk", "legal", "technical", "constraint", "limitation"),
            "Riscos, restricoes tecnicas, legais e operacionais.",
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
