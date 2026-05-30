from app.domain.deep_research import evaluate_research_coverage, deep_research_blockers
from app.domain.schemas import EvidenceLevel, Finding, Source


def test_deep_research_uses_generic_facets_to_catch_domain_depth() -> None:
    coverage = evaluate_research_coverage(
        idea="Quero criar um sistema de mercado para Path of Exile",
        sources=[
            Source(
                title="Path of Exile Developer Docs",
                url="https://www.pathofexile.com/developer/docs",
                source_type="official_documentation",
                reliability_score=95,
                notes="API, public stash, currency exchange e rate limit.",
            ),
            Source(
                title="Awakened PoE Trade GitHub Repository",
                url="https://github.com/SnosMe/awakened-poe-trade",
                source_type="competitor_repository",
                reliability_score=85,
                notes="Repositorio GitHub de concorrente.",
            ),
        ],
        findings=[
            Finding(
                statement="A API oficial permite coleta de market data, mas ainda falta entender patch, meta builds, item weight e affix.",
                evidence_level=EvidenceLevel.strong,
                source_titles=["Path of Exile Developer Docs"],
                confidence_score=90,
            )
        ],
    )

    assert "primary_authoritative_sources" in coverage.covered_facets
    assert "causal_and_temporal_dynamics" in coverage.covered_facets
    assert "domain_object_taxonomy" in coverage.covered_facets
    assert "open_implementations_and_repos" in coverage.covered_facets
    assert coverage.concrete_source_count == 2


def test_deep_research_blocks_shallow_projects() -> None:
    coverage = evaluate_research_coverage(
        idea="Quero criar um sistema para tornar alguem um bom hacker etico",
        sources=[
            Source(
                title="OWASP Web Security Testing Guide",
                url="https://owasp.org/www-project-web-security-testing-guide/",
                source_type="official_testing_guide",
                reliability_score=94,
                notes="OWASP WSTG para web security.",
            )
        ],
        findings=[],
    )

    blockers = deep_research_blockers(coverage)

    assert any("fontes concretas insuficientes" in blocker for blocker in blockers)
    assert any("faceta critica sem cobertura" in blocker for blocker in blockers)
