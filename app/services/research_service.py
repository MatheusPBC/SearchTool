from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.orchestrator import ResearchOrchestrator
from app.agents.workflow import build_workflow_step
from app.domain.repository import (
    answer_project_question,
    create_project_finding,
    create_project_source,
    delete_finding,
    create_research_run,
    get_project_report,
    ingest_project_source,
    list_project_findings,
    list_project_hypotheses,
    list_project_questions,
    list_project_sources,
    list_projects,
    list_research_runs,
    plan_next_research_run,
    recalculate_project_status,
    save_project_report,
    update_hypothesis_evidence,
    update_research_run,
)
from app.domain.schemas import (
    AnswerQuestionRequest,
    CreateFindingRequest,
    CreateProjectRequest,
    CreateResearchRunRequest,
    CreateSourceRequest,
    IngestSourceRequest,
    ResearchRunStatus,
    UpdateHypothesisEvidenceRequest,
    UpdateResearchRunRequest,
)


class ResearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_project(self, idea: str, target_confidence: int = 85) -> dict:
        payload = CreateProjectRequest(idea=idea, target_confidence=target_confidence)
        report = ResearchOrchestrator().run_initial_research(
            idea=payload.idea,
            target_confidence=payload.target_confidence,
        )
        return save_project_report(self.db, report).model_dump(mode="json")

    def list_projects(self) -> list[dict]:
        return [
            {
                "project_id": project.id,
                "idea": project.idea,
                "confidence_score": project.confidence_score,
                "target_confidence": project.target_confidence,
                "can_finalize": project.can_finalize,
            }
            for project in list_projects(self.db)
        ]

    def show_project(self, project_id: UUID) -> dict:
        report = get_project_report(self.db, project_id)
        if report is None:
            raise ValueError("Project not found")
        return report.model_dump(mode="json")

    def list_questions(self, project_id: UUID) -> list[dict]:
        if get_project_report(self.db, project_id) is None:
            raise ValueError("Project not found")
        return [item.model_dump(mode="json") for item in list_project_questions(self.db, project_id)]

    def list_sources(self, project_id: UUID) -> list[dict]:
        if get_project_report(self.db, project_id) is None:
            raise ValueError("Project not found")
        return [item.model_dump(mode="json") for item in list_project_sources(self.db, project_id)]

    def create_source(
        self,
        project_id: UUID,
        title: str,
        source_type: str,
        reliability_score: int,
        notes: str,
        url: str | None = None,
    ) -> dict:
        source = create_project_source(
            self.db,
            project_id,
            CreateSourceRequest(
                title=title,
                url=url,
                source_type=source_type,
                reliability_score=reliability_score,
                notes=notes,
            ),
        )
        if source is None:
            raise ValueError("Project not found")
        return source.model_dump(mode="json")

    def ingest_source(
        self,
        project_id: UUID,
        title: str,
        source_type: str,
        reliability_score: int,
        notes: str,
        content: str,
        url: str | None = None,
        max_findings: int = 5,
    ) -> dict:
        result = ingest_project_source(
            self.db,
            project_id,
            IngestSourceRequest(
                title=title,
                url=url,
                source_type=source_type,
                reliability_score=reliability_score,
                notes=notes,
                content=content,
                max_findings=max_findings,
            ),
        )
        if result is None:
            raise ValueError("Project not found")
        return result.model_dump(mode="json")

    def list_findings(self, project_id: UUID) -> list[dict]:
        if get_project_report(self.db, project_id) is None:
            raise ValueError("Project not found")
        return [item.model_dump(mode="json") for item in list_project_findings(self.db, project_id)]

    def create_finding(
        self,
        project_id: UUID,
        statement: str,
        evidence_level: str,
        confidence_score: int,
        source_titles: list[str] | None = None,
    ) -> dict:
        finding = create_project_finding(
            self.db,
            project_id,
            CreateFindingRequest(
                statement=statement,
                evidence_level=evidence_level,
                source_titles=source_titles or [],
                confidence_score=confidence_score,
            ),
        )
        if finding is None:
            raise ValueError("Project not found")
        return finding.model_dump(mode="json")

    def delete_finding(self, project_id: UUID, finding_id: int) -> dict:
        deleted = delete_finding(self.db, project_id, finding_id)
        if not deleted:
            raise ValueError("Finding not found")
        return {"deleted": True, "project_id": str(project_id), "finding_id": finding_id}

    def list_hypotheses(self, project_id: UUID) -> list[dict]:
        if get_project_report(self.db, project_id) is None:
            raise ValueError("Project not found")
        return [item.model_dump(mode="json") for item in list_project_hypotheses(self.db, project_id)]

    def update_hypothesis(
        self,
        project_id: UUID,
        hypothesis_id: int,
        evidence_level: str,
        confidence_score: int,
    ) -> dict:
        hypothesis = update_hypothesis_evidence(
            self.db,
            project_id,
            hypothesis_id,
            UpdateHypothesisEvidenceRequest(
                evidence_level=evidence_level,
                confidence_score=confidence_score,
            ),
        )
        if hypothesis is None:
            raise ValueError("Hypothesis not found")
        return hypothesis.model_dump(mode="json")

    def answer_question(self, project_id: UUID, question_id: int, answered: bool = True) -> dict:
        question = answer_project_question(
            self.db,
            project_id,
            question_id,
            AnswerQuestionRequest(answered=answered),
        )
        if question is None:
            raise ValueError("Question not found")
        return question.model_dump(mode="json")

    def list_runs(self, project_id: UUID) -> list[dict]:
        runs = list_research_runs(self.db, project_id)
        if runs is None:
            raise ValueError("Project not found")
        return [item.model_dump(mode="json") for item in runs]

    def create_run(
        self,
        project_id: UUID,
        objective: str,
        question_ids: list[int] | None = None,
    ) -> dict:
        run = create_research_run(
            self.db,
            project_id,
            CreateResearchRunRequest(objective=objective, question_ids=question_ids or []),
        )
        if run is None:
            raise ValueError("Project not found")
        return run.model_dump(mode="json")

    def update_run(
        self,
        project_id: UUID,
        run_id: int,
        status: str,
        notes: str = "",
    ) -> dict:
        run = update_research_run(
            self.db,
            project_id,
            run_id,
            UpdateResearchRunRequest(status=ResearchRunStatus(status), notes=notes),
        )
        if run is None:
            raise ValueError("Research run not found")
        return run.model_dump(mode="json")

    def plan_next_run(self, project_id: UUID) -> dict:
        planned = plan_next_research_run(self.db, project_id)
        if planned is None:
            raise ValueError("Project not found")
        return planned.model_dump(mode="json")

    def next_action(self, project_id: UUID) -> dict:
        report = get_project_report(self.db, project_id)
        if report is None:
            raise ValueError("Project not found")

        planned = plan_next_research_run(self.db, project_id)
        if planned is None:
            raise ValueError("Could not plan next run")

        return {
            "project_id": str(project_id),
            "confidence_score": report.confidence_score,
            "target_confidence": report.target_confidence,
            "can_finalize": report.can_finalize,
            "blockers": report.blockers,
            "recommended_next_run": planned.model_dump(mode="json"),
            "suggested_agent_instruction": (
                "Use the recommended_next_run objective and planned_questions to gather sources. "
                "Then call ingest_source for each relevant source and recalculate."
            ),
        }

    def advance_workflow(self, project_id: UUID) -> dict:
        report = recalculate_project_status(self.db, project_id)
        if report is None:
            raise ValueError("Project not found")

        open_questions = list_project_questions(self.db, project_id)
        open_questions = [question for question in open_questions if not question.answered]
        planned = None
        if not report.can_finalize:
            planned = plan_next_research_run(self.db, project_id)
            if planned is None:
                raise ValueError("Could not plan next run")

        return build_workflow_step(report, open_questions, planned)

    def recalculate(self, project_id: UUID) -> dict:
        report = recalculate_project_status(self.db, project_id)
        if report is None:
            raise ValueError("Project not found")
        return report.model_dump(mode="json")
