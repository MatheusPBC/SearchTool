from app.agents.critic import Critic
from app.agents.knowledge_extractor import KnowledgeExtractor
from app.agents.mvp_builder import MvpBuilder
from app.agents.research_planner import ResearchPlanner
from app.agents.source_finder import SourceFinder
from app.domain.confidence import calculate_confidence, find_completion_blockers
from app.domain.schemas import ProjectReport


class ResearchOrchestrator:
    def __init__(self) -> None:
        self.research_planner = ResearchPlanner()
        self.source_finder = SourceFinder()
        self.knowledge_extractor = KnowledgeExtractor()
        self.critic = Critic()
        self.mvp_builder = MvpBuilder()

    def run_initial_research(self, idea: str, target_confidence: int) -> ProjectReport:
        questions = self.research_planner.generate_questions(idea)
        sources = self.source_finder.find_seed_sources(idea)
        findings = self.knowledge_extractor.extract_findings(idea, sources)
        hypotheses = self.critic.create_hypotheses()
        domain_map = self.knowledge_extractor.extract_relationships()
        mvp = self.mvp_builder.build_plan()
        decisions = self.mvp_builder.make_decisions()

        competitors = [
            "Ferramentas especializadas do dominio ainda precisam ser pesquisadas",
            "Planilhas, dashboards e alertas manuais usados como substitutos",
        ]

        confidence_score = calculate_confidence(
            sources=sources,
            findings=findings,
            hypotheses=hypotheses,
            questions=questions,
        )
        blockers = find_completion_blockers(
            idea=idea,
            target_confidence=target_confidence,
            confidence_score=confidence_score,
            sources=sources,
            findings=findings,
            questions=questions,
            hypotheses=hypotheses,
            competitors=competitors,
        )

        return ProjectReport(
            idea=idea,
            confidence_score=confidence_score,
            target_confidence=target_confidence,
            can_finalize=len(blockers) == 0,
            domain_map=domain_map,
            critical_questions=questions,
            sources=sources,
            competitors=competitors,
            findings=findings,
            hypotheses=hypotheses,
            decisions=decisions,
            mvp=mvp,
            blockers=blockers,
        )
