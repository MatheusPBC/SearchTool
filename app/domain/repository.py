from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agents.run_planner import RunPlanner
from app.agents.source_ingestor import SourceIngestor
from app.domain.models import (
    ArchitectureItemModel,
    BacklogItemModel,
    BlockerModel,
    CompetitorModel,
    DecisionModel,
    FindingModel,
    HypothesisModel,
    OpenQuestionModel,
    ProjectModel,
    RelationshipModel,
    ResearchRunFindingModel,
    ResearchRunModel,
    ResearchRunQuestionModel,
    ResearchRunSourceModel,
    RiskModel,
    SourceModel,
)
from app.domain.schemas import (
    AnswerQuestionRequest,
    CreateFindingRequest,
    CreateSourceRequest,
    Decision,
    EvidenceLevel,
    Finding,
    FindingRecord,
    Hypothesis,
    HypothesisRecord,
    IngestSourceRequest,
    IngestSourceResult,
    MvpPlan,
    OpenQuestion,
    OpenQuestionRecord,
    PlannedResearchRun,
    ProjectReport,
    ResearchRun,
    ResearchRunStatus,
    Relationship,
    Source,
    SourceRecord,
    CreateResearchRunRequest,
    UpdateResearchRunRequest,
    UpdateHypothesisEvidenceRequest,
)
from app.domain.confidence import calculate_confidence, find_completion_blockers


def save_project_report(db: Session, report: ProjectReport) -> ProjectReport:
    project_id = str(report.project_id)
    project = ProjectModel(
        id=project_id,
        idea=report.idea,
        confidence_score=report.confidence_score,
        target_confidence=report.target_confidence,
        can_finalize=report.can_finalize,
        recommended_mvp=report.mvp.recommended_mvp,
    )

    project.sources = [
        SourceModel(
            title=source.title,
            url=source.url,
            source_type=source.source_type,
            reliability_score=source.reliability_score,
            notes=source.notes,
        )
        for source in report.sources
    ]
    project.findings = [
        FindingModel(
            statement=finding.statement,
            evidence_level=finding.evidence_level.value,
            source_titles="\n".join(finding.source_titles),
            confidence_score=finding.confidence_score,
        )
        for finding in report.findings
    ]
    project.hypotheses = [
        HypothesisModel(
            statement=hypothesis.statement,
            evidence_level=hypothesis.evidence_level.value,
            confidence_score=hypothesis.confidence_score,
            falsification_questions="\n".join(hypothesis.falsification_questions),
        )
        for hypothesis in report.hypotheses
    ]
    project.questions = [
        OpenQuestionModel(
            question=question.question,
            criticality=question.criticality,
            impact_on_mvp=question.impact_on_mvp,
            answered=question.answered,
        )
        for question in report.critical_questions
    ]
    project.relationships = [
        RelationshipModel(
            source=relationship.source,
            target=relationship.target,
            relation=relationship.relation,
            confidence_score=relationship.confidence_score,
        )
        for relationship in report.domain_map
    ]
    project.decisions = [
        DecisionModel(
            decision=decision.decision,
            rationale=decision.rationale,
            confidence_score=decision.confidence_score,
        )
        for decision in report.decisions
    ]
    project.competitors = [CompetitorModel(name=competitor) for competitor in report.competitors]
    project.architecture_items = [
        ArchitectureItemModel(item=item) for item in report.mvp.architecture
    ]
    project.backlog_items = [BacklogItemModel(item=item) for item in report.mvp.backlog]
    project.risks = [RiskModel(risk=risk) for risk in report.mvp.risks]
    project.blockers = [BlockerModel(blocker=blocker) for blocker in report.blockers]

    db.add(project)
    db.commit()
    db.refresh(project)

    return report


def list_projects(db: Session) -> list[ProjectModel]:
    return list(db.scalars(select(ProjectModel).order_by(ProjectModel.id)))


def get_project_report(db: Session, project_id: UUID) -> ProjectReport | None:
    project = db.scalar(
        select(ProjectModel)
        .where(ProjectModel.id == str(project_id))
        .options(
            selectinload(ProjectModel.sources),
            selectinload(ProjectModel.findings),
            selectinload(ProjectModel.hypotheses),
            selectinload(ProjectModel.questions),
            selectinload(ProjectModel.relationships),
            selectinload(ProjectModel.decisions),
            selectinload(ProjectModel.competitors),
            selectinload(ProjectModel.architecture_items),
            selectinload(ProjectModel.backlog_items),
            selectinload(ProjectModel.risks),
            selectinload(ProjectModel.blockers),
        )
    )

    if project is None:
        return None

    return ProjectReport(
        project_id=UUID(project.id),
        idea=project.idea,
        confidence_score=project.confidence_score,
        target_confidence=project.target_confidence,
        can_finalize=project.can_finalize,
        domain_map=[
            Relationship(
                source=item.source,
                target=item.target,
                relation=item.relation,
                confidence_score=item.confidence_score,
            )
            for item in project.relationships
        ],
        critical_questions=[
            OpenQuestion(
                question=item.question,
                criticality=item.criticality,
                impact_on_mvp=item.impact_on_mvp,
                answered=item.answered,
            )
            for item in project.questions
        ],
        sources=[
            Source(
                title=item.title,
                url=item.url,
                source_type=item.source_type,
                reliability_score=item.reliability_score,
                notes=item.notes,
            )
            for item in project.sources
        ],
        competitors=[item.name for item in project.competitors],
        findings=[
            Finding(
                statement=item.statement,
                evidence_level=EvidenceLevel(item.evidence_level),
                source_titles=_split_lines(item.source_titles),
                confidence_score=item.confidence_score,
            )
            for item in project.findings
        ],
        hypotheses=[
            Hypothesis(
                statement=item.statement,
                evidence_level=EvidenceLevel(item.evidence_level),
                confidence_score=item.confidence_score,
                falsification_questions=_split_lines(item.falsification_questions),
            )
            for item in project.hypotheses
        ],
        decisions=[
            Decision(
                decision=item.decision,
                rationale=item.rationale,
                confidence_score=item.confidence_score,
            )
            for item in project.decisions
        ],
        mvp=MvpPlan(
            recommended_mvp=project.recommended_mvp,
            architecture=[item.item for item in project.architecture_items],
            backlog=[item.item for item in project.backlog_items],
            risks=[item.risk for item in project.risks],
        ),
        blockers=[item.blocker for item in project.blockers],
    )


def list_project_questions(db: Session, project_id: UUID) -> list[OpenQuestionRecord]:
    questions = db.scalars(
        select(OpenQuestionModel)
        .where(OpenQuestionModel.project_id == str(project_id))
        .order_by(OpenQuestionModel.criticality.desc(), OpenQuestionModel.id)
    )

    return [
        OpenQuestionRecord(
            id=item.id,
            question=item.question,
            criticality=item.criticality,
            impact_on_mvp=item.impact_on_mvp,
            answered=item.answered,
        )
        for item in questions
    ]


def list_project_sources(db: Session, project_id: UUID) -> list[SourceRecord]:
    sources = db.scalars(
        select(SourceModel)
        .where(SourceModel.project_id == str(project_id))
        .order_by(SourceModel.reliability_score.desc(), SourceModel.id)
    )

    return [
        SourceRecord(
            id=item.id,
            title=item.title,
            url=item.url,
            source_type=item.source_type,
            reliability_score=item.reliability_score,
            notes=item.notes,
        )
        for item in sources
    ]


def create_project_source(
    db: Session,
    project_id: UUID,
    payload: CreateSourceRequest,
) -> SourceRecord | None:
    if not _project_exists(db, project_id):
        return None

    source = SourceModel(
        project_id=str(project_id),
        title=payload.title,
        url=payload.url,
        source_type=payload.source_type,
        reliability_score=payload.reliability_score,
        notes=payload.notes,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    _attach_source_to_latest_running_run(db, project_id, source.id)
    recalculate_project_status(db, project_id)

    return SourceRecord(
        id=source.id,
        title=source.title,
        url=source.url,
        source_type=source.source_type,
        reliability_score=source.reliability_score,
        notes=source.notes,
    )


def list_project_findings(db: Session, project_id: UUID) -> list[FindingRecord]:
    findings = db.scalars(
        select(FindingModel)
        .where(FindingModel.project_id == str(project_id))
        .order_by(FindingModel.confidence_score.desc(), FindingModel.id)
    )

    return [
        FindingRecord(
            id=item.id,
            statement=item.statement,
            evidence_level=EvidenceLevel(item.evidence_level),
            source_titles=_split_lines(item.source_titles),
            confidence_score=item.confidence_score,
        )
        for item in findings
    ]


def create_project_finding(
    db: Session,
    project_id: UUID,
    payload: CreateFindingRequest,
) -> FindingRecord | None:
    if not _project_exists(db, project_id):
        return None

    finding = FindingModel(
        project_id=str(project_id),
        statement=payload.statement,
        evidence_level=payload.evidence_level.value,
        source_titles="\n".join(payload.source_titles),
        confidence_score=payload.confidence_score,
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    _attach_finding_to_latest_running_run(db, project_id, finding.id)
    recalculate_project_status(db, project_id)

    return FindingRecord(
        id=finding.id,
        statement=finding.statement,
        evidence_level=EvidenceLevel(finding.evidence_level),
        source_titles=_split_lines(finding.source_titles),
        confidence_score=finding.confidence_score,
    )


def delete_finding(db: Session, project_id: UUID, finding_id: int) -> bool:
    finding = db.scalar(
        select(FindingModel).where(
            FindingModel.project_id == str(project_id),
            FindingModel.id == finding_id,
        )
    )
    if finding is None:
        return False

    db.delete(finding)
    db.commit()
    recalculate_project_status(db, project_id)
    return True


def ingest_project_source(
    db: Session,
    project_id: UUID,
    payload: IngestSourceRequest,
) -> IngestSourceResult | None:
    if not _project_exists(db, project_id):
        return None

    source = create_project_source(
        db,
        project_id,
        CreateSourceRequest(
            title=payload.title,
            url=payload.url,
            source_type=payload.source_type,
            reliability_score=payload.reliability_score,
            notes=payload.notes,
        ),
    )
    if source is None:
        return None

    extraction = SourceIngestor().extract_findings(
        title=payload.title,
        source_type=payload.source_type,
        content=payload.content,
        max_findings=payload.max_findings,
    )

    findings: list[FindingRecord] = []
    for finding in extraction.findings:
        created = create_project_finding(
            db,
            project_id,
            CreateFindingRequest(
                statement=finding.statement,
                evidence_level=finding.evidence_level,
                source_titles=finding.source_titles,
                confidence_score=finding.confidence_score,
            ),
        )
        if created is not None:
            findings.append(created)

    recalculate_project_status(db, project_id)

    return IngestSourceResult(
        source=source,
        findings=findings,
        extraction_notes=extraction.notes,
    )


def answer_project_question(
    db: Session,
    project_id: UUID,
    question_id: int,
    payload: AnswerQuestionRequest,
) -> OpenQuestionRecord | None:
    question = db.scalar(
        select(OpenQuestionModel).where(
            OpenQuestionModel.project_id == str(project_id),
            OpenQuestionModel.id == question_id,
        )
    )

    if question is None:
        return None

    question.answered = payload.answered
    db.commit()
    db.refresh(question)
    recalculate_project_status(db, project_id)

    return OpenQuestionRecord(
        id=question.id,
        question=question.question,
        criticality=question.criticality,
        impact_on_mvp=question.impact_on_mvp,
        answered=question.answered,
    )


def list_project_hypotheses(db: Session, project_id: UUID) -> list[HypothesisRecord]:
    hypotheses = db.scalars(
        select(HypothesisModel)
        .where(HypothesisModel.project_id == str(project_id))
        .order_by(HypothesisModel.confidence_score, HypothesisModel.id)
    )

    return [
        HypothesisRecord(
            id=item.id,
            statement=item.statement,
            evidence_level=EvidenceLevel(item.evidence_level),
            confidence_score=item.confidence_score,
            falsification_questions=_split_lines(item.falsification_questions),
        )
        for item in hypotheses
    ]


def update_hypothesis_evidence(
    db: Session,
    project_id: UUID,
    hypothesis_id: int,
    payload: UpdateHypothesisEvidenceRequest,
) -> HypothesisRecord | None:
    hypothesis = db.scalar(
        select(HypothesisModel).where(
            HypothesisModel.project_id == str(project_id),
            HypothesisModel.id == hypothesis_id,
        )
    )

    if hypothesis is None:
        return None

    hypothesis.evidence_level = payload.evidence_level.value
    hypothesis.confidence_score = payload.confidence_score
    db.commit()
    db.refresh(hypothesis)
    recalculate_project_status(db, project_id)

    return HypothesisRecord(
        id=hypothesis.id,
        statement=hypothesis.statement,
        evidence_level=EvidenceLevel(hypothesis.evidence_level),
        confidence_score=hypothesis.confidence_score,
        falsification_questions=_split_lines(hypothesis.falsification_questions),
    )


def recalculate_project_status(db: Session, project_id: UUID) -> ProjectReport | None:
    report = get_project_report(db, project_id)
    if report is None:
        return None

    confidence_score = calculate_confidence(
        sources=report.sources,
        findings=report.findings,
        hypotheses=report.hypotheses,
        questions=report.critical_questions,
    )
    blockers = find_completion_blockers(
        idea=report.idea,
        target_confidence=report.target_confidence,
        confidence_score=confidence_score,
        sources=report.sources,
        findings=report.findings,
        questions=report.critical_questions,
        hypotheses=report.hypotheses,
        competitors=report.competitors,
    )

    project = db.scalar(select(ProjectModel).where(ProjectModel.id == str(project_id)))
    if project is None:
        return None

    project.confidence_score = confidence_score
    project.can_finalize = len(blockers) == 0
    project.blockers = [BlockerModel(blocker=blocker) for blocker in blockers]
    db.commit()

    return get_project_report(db, project_id)


def create_research_run(
    db: Session,
    project_id: UUID,
    payload: CreateResearchRunRequest,
) -> ResearchRun | None:
    if not _project_exists(db, project_id):
        return None

    valid_question_ids = _valid_project_question_ids(db, project_id, payload.question_ids)
    run = ResearchRunModel(
        project_id=str(project_id),
        status=ResearchRunStatus.planned.value,
        objective=payload.objective,
        notes="",
    )
    run.questions = [
        ResearchRunQuestionModel(question_id=question_id) for question_id in valid_question_ids
    ]

    db.add(run)
    db.commit()
    db.refresh(run)

    return _run_to_schema(db, run)


def list_research_runs(db: Session, project_id: UUID) -> list[ResearchRun] | None:
    if not _project_exists(db, project_id):
        return None

    runs = db.scalars(
        select(ResearchRunModel)
        .where(ResearchRunModel.project_id == str(project_id))
        .options(
            selectinload(ResearchRunModel.questions),
            selectinload(ResearchRunModel.sources),
            selectinload(ResearchRunModel.findings),
        )
        .order_by(ResearchRunModel.id.desc())
    )

    return [_run_to_schema(db, run) for run in runs]


def update_research_run(
    db: Session,
    project_id: UUID,
    run_id: int,
    payload: UpdateResearchRunRequest,
) -> ResearchRun | None:
    run = db.scalar(
        select(ResearchRunModel)
        .where(
            ResearchRunModel.project_id == str(project_id),
            ResearchRunModel.id == run_id,
        )
        .options(
            selectinload(ResearchRunModel.questions),
            selectinload(ResearchRunModel.sources),
            selectinload(ResearchRunModel.findings),
        )
    )

    if run is None:
        return None

    run.status = payload.status.value
    run.notes = payload.notes
    db.commit()
    db.refresh(run)

    return _run_to_schema(db, run)


def plan_next_research_run(db: Session, project_id: UUID) -> PlannedResearchRun | None:
    report = get_project_report(db, project_id)
    if report is None:
        return None

    open_questions = _list_open_question_records(db, project_id)
    plan = RunPlanner().plan_next_run(report=report, open_questions=open_questions)

    run = create_research_run(
        db,
        project_id,
        CreateResearchRunRequest(
            objective=plan.objective,
            question_ids=plan.question_ids,
        ),
    )
    if run is None:
        return None

    return PlannedResearchRun(
        run=run,
        rationale=plan.rationale,
        targeted_blockers=plan.targeted_blockers,
    )


def _split_lines(value: str) -> list[str]:
    return [line for line in value.splitlines() if line]


def _project_exists(db: Session, project_id: UUID) -> bool:
    return db.scalar(select(ProjectModel.id).where(ProjectModel.id == str(project_id))) is not None


def _valid_project_question_ids(db: Session, project_id: UUID, question_ids: list[int]) -> list[int]:
    if not question_ids:
        return []

    return list(
        db.scalars(
            select(OpenQuestionModel.id).where(
                OpenQuestionModel.project_id == str(project_id),
                OpenQuestionModel.id.in_(question_ids),
            )
        )
    )


def _list_open_question_records(db: Session, project_id: UUID) -> list[OpenQuestionRecord]:
    question_rows = db.scalars(
        select(OpenQuestionModel)
        .where(
            OpenQuestionModel.project_id == str(project_id),
            OpenQuestionModel.answered.is_(False),
        )
        .order_by(OpenQuestionModel.criticality.desc(), OpenQuestionModel.id)
    )

    return [
        OpenQuestionRecord(
            id=question.id,
            question=question.question,
            criticality=question.criticality,
            impact_on_mvp=question.impact_on_mvp,
            answered=question.answered,
        )
        for question in question_rows
    ]


def _run_to_schema(db: Session, run: ResearchRunModel) -> ResearchRun:
    question_ids = [item.question_id for item in run.questions]
    questions_by_id = {}
    if question_ids:
        question_rows = db.scalars(
            select(OpenQuestionModel).where(OpenQuestionModel.id.in_(question_ids))
        )
        questions_by_id = {row.id: row.question for row in question_rows}

    return ResearchRun(
        id=run.id,
        project_id=UUID(run.project_id),
        status=ResearchRunStatus(run.status),
        objective=run.objective,
        planned_questions=[
            questions_by_id[question_id]
            for question_id in question_ids
            if question_id in questions_by_id
        ],
        generated_source_ids=[item.source_id for item in run.sources],
        generated_finding_ids=[item.finding_id for item in run.findings],
        notes=run.notes,
    )


def _attach_source_to_latest_running_run(db: Session, project_id: UUID, source_id: int) -> None:
    run = _latest_running_run(db, project_id)
    if run is None:
        return

    db.add(ResearchRunSourceModel(run_id=run.id, source_id=source_id))
    db.commit()


def _attach_finding_to_latest_running_run(db: Session, project_id: UUID, finding_id: int) -> None:
    run = _latest_running_run(db, project_id)
    if run is None:
        return

    db.add(ResearchRunFindingModel(run_id=run.id, finding_id=finding_id))
    db.commit()


def _latest_running_run(db: Session, project_id: UUID) -> ResearchRunModel | None:
    return db.scalar(
        select(ResearchRunModel)
        .where(
            ResearchRunModel.project_id == str(project_id),
            ResearchRunModel.status == ResearchRunStatus.running.value,
        )
        .order_by(ResearchRunModel.id.desc())
    )
