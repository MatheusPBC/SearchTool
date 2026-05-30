from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, init_db
from app.agents.orchestrator import ResearchOrchestrator
from app.domain.repository import (
    answer_project_question,
    create_research_run,
    create_project_finding,
    create_project_source,
    get_project_report,
    ingest_project_source,
    list_research_runs,
    list_project_findings,
    list_project_hypotheses,
    list_project_questions,
    list_project_sources,
    list_projects,
    plan_next_research_run,
    recalculate_project_status,
    save_project_report,
    update_research_run,
    update_hypothesis_evidence,
)
from app.domain.schemas import (
    AnswerQuestionRequest,
    CreateFindingRequest,
    CreateProjectRequest,
    CreateResearchRunRequest,
    CreateSourceRequest,
    FindingRecord,
    HypothesisRecord,
    IngestSourceRequest,
    IngestSourceResult,
    OpenQuestionRecord,
    PlannedResearchRun,
    ProjectReport,
    ProjectSummary,
    ResearchRun,
    SourceRecord,
    UpdateResearchRunRequest,
    UpdateHypothesisEvidenceRequest,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Autonomous Research-to-MVP Agent",
    version="0.1.0",
    description="Research agent that turns vague ideas into structured MVP plans.",
    lifespan=lifespan,
)

init_db()

orchestrator = ResearchOrchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/projects", response_model=ProjectReport)
def create_project(payload: CreateProjectRequest, db: Session = Depends(get_db)) -> ProjectReport:
    report = orchestrator.run_initial_research(
        idea=payload.idea,
        target_confidence=payload.target_confidence,
    )
    return save_project_report(db, report)


@app.get("/projects", response_model=list[ProjectSummary])
def get_projects(db: Session = Depends(get_db)) -> list[ProjectSummary]:
    return [
        ProjectSummary(
            project_id=UUID(project.id),
            idea=project.idea,
            confidence_score=project.confidence_score,
            target_confidence=project.target_confidence,
            can_finalize=project.can_finalize,
        )
        for project in list_projects(db)
    ]


@app.get("/projects/{project_id}", response_model=ProjectReport)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectReport:
    report = get_project_report(db, project_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return report


@app.get("/projects/{project_id}/questions", response_model=list[OpenQuestionRecord])
def get_project_questions(project_id: UUID, db: Session = Depends(get_db)) -> list[OpenQuestionRecord]:
    if get_project_report(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_questions(db, project_id)


@app.patch(
    "/projects/{project_id}/questions/{question_id}",
    response_model=OpenQuestionRecord,
)
def patch_project_question(
    project_id: UUID,
    question_id: int,
    payload: AnswerQuestionRequest,
    db: Session = Depends(get_db),
) -> OpenQuestionRecord:
    question = answer_project_question(db, project_id, question_id, payload)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@app.get("/projects/{project_id}/sources", response_model=list[SourceRecord])
def get_project_sources(project_id: UUID, db: Session = Depends(get_db)) -> list[SourceRecord]:
    if get_project_report(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_sources(db, project_id)


@app.post("/projects/{project_id}/sources", response_model=SourceRecord)
def post_project_source(
    project_id: UUID,
    payload: CreateSourceRequest,
    db: Session = Depends(get_db),
) -> SourceRecord:
    source = create_project_source(db, project_id, payload)
    if source is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return source


@app.post("/projects/{project_id}/ingest-source", response_model=IngestSourceResult)
def post_project_ingest_source(
    project_id: UUID,
    payload: IngestSourceRequest,
    db: Session = Depends(get_db),
) -> IngestSourceResult:
    result = ingest_project_source(db, project_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@app.get("/projects/{project_id}/runs", response_model=list[ResearchRun])
def get_project_runs(project_id: UUID, db: Session = Depends(get_db)) -> list[ResearchRun]:
    runs = list_research_runs(db, project_id)
    if runs is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return runs


@app.post("/projects/{project_id}/runs", response_model=ResearchRun)
def post_project_run(
    project_id: UUID,
    payload: CreateResearchRunRequest,
    db: Session = Depends(get_db),
) -> ResearchRun:
    run = create_research_run(db, project_id, payload)
    if run is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return run


@app.patch("/projects/{project_id}/runs/{run_id}", response_model=ResearchRun)
def patch_project_run(
    project_id: UUID,
    run_id: int,
    payload: UpdateResearchRunRequest,
    db: Session = Depends(get_db),
) -> ResearchRun:
    run = update_research_run(db, project_id, run_id, payload)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@app.post("/projects/{project_id}/plan-next-run", response_model=PlannedResearchRun)
def post_project_next_run(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> PlannedResearchRun:
    planned = plan_next_research_run(db, project_id)
    if planned is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return planned


@app.get("/projects/{project_id}/findings", response_model=list[FindingRecord])
def get_project_findings(project_id: UUID, db: Session = Depends(get_db)) -> list[FindingRecord]:
    if get_project_report(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_findings(db, project_id)


@app.post("/projects/{project_id}/findings", response_model=FindingRecord)
def post_project_finding(
    project_id: UUID,
    payload: CreateFindingRequest,
    db: Session = Depends(get_db),
) -> FindingRecord:
    finding = create_project_finding(db, project_id, payload)
    if finding is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return finding


@app.get("/projects/{project_id}/hypotheses", response_model=list[HypothesisRecord])
def get_project_hypotheses(
    project_id: UUID,
    db: Session = Depends(get_db),
) -> list[HypothesisRecord]:
    if get_project_report(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_hypotheses(db, project_id)


@app.patch(
    "/projects/{project_id}/hypotheses/{hypothesis_id}",
    response_model=HypothesisRecord,
)
def patch_project_hypothesis(
    project_id: UUID,
    hypothesis_id: int,
    payload: UpdateHypothesisEvidenceRequest,
    db: Session = Depends(get_db),
) -> HypothesisRecord:
    hypothesis = update_hypothesis_evidence(db, project_id, hypothesis_id, payload)
    if hypothesis is None:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@app.post("/projects/{project_id}/recalculate", response_model=ProjectReport)
def recalculate_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectReport:
    report = recalculate_project_status(db, project_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return report
