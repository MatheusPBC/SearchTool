from app.agents.orchestrator import ResearchOrchestrator


def test_initial_research_does_not_finalize_with_open_critical_questions() -> None:
    orchestrator = ResearchOrchestrator()

    report = orchestrator.run_initial_research(
        idea="Quero criar um sistema de mercado para Path of Exile",
        target_confidence=85,
    )

    assert report.can_finalize is False
    assert report.confidence_score < 85
    assert "existem perguntas criticas sem resposta" in report.blockers
    assert "existem hipoteses sem evidencia suficiente" in report.blockers


def test_initial_research_returns_mvp_sections() -> None:
    orchestrator = ResearchOrchestrator()

    report = orchestrator.run_initial_research(
        idea="Quero construir uma plataforma de pesquisa autonoma",
        target_confidence=85,
    )

    assert report.critical_questions
    assert report.sources
    assert report.findings
    assert report.hypotheses
    assert report.domain_map
    assert report.mvp.backlog

