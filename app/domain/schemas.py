from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvidenceLevel(str, Enum):
    none = "none"
    weak = "weak"
    moderate = "moderate"
    strong = "strong"


class ResearchRunStatus(str, Enum):
    planned = "planned"
    running = "running"
    completed = "completed"
    blocked = "blocked"


class CreateProjectRequest(BaseModel):
    idea: str = Field(min_length=10)
    target_confidence: int = Field(default=85, ge=1, le=100)


class Source(BaseModel):
    title: str
    url: str | None = None
    source_type: str
    reliability_score: int = Field(ge=0, le=100)
    notes: str


class SourceRecord(Source):
    id: int


class CreateSourceRequest(Source):
    pass


class Finding(BaseModel):
    statement: str
    evidence_level: EvidenceLevel
    source_titles: list[str] = Field(default_factory=list)
    confidence_score: int = Field(ge=0, le=100)


class FindingRecord(Finding):
    id: int


class CreateFindingRequest(Finding):
    pass


class IngestSourceRequest(CreateSourceRequest):
    content: str = Field(min_length=50)
    max_findings: int = Field(default=5, ge=1, le=10)


class IngestSourceResult(BaseModel):
    source: SourceRecord
    findings: list[FindingRecord]
    extraction_notes: str


class Hypothesis(BaseModel):
    statement: str
    evidence_level: EvidenceLevel
    confidence_score: int = Field(ge=0, le=100)
    falsification_questions: list[str] = Field(default_factory=list)


class HypothesisRecord(Hypothesis):
    id: int


class UpdateHypothesisEvidenceRequest(BaseModel):
    evidence_level: EvidenceLevel
    confidence_score: int = Field(ge=0, le=100)


class OpenQuestion(BaseModel):
    question: str
    criticality: int = Field(ge=1, le=5)
    impact_on_mvp: str
    answered: bool = False


class OpenQuestionRecord(OpenQuestion):
    id: int


class AnswerQuestionRequest(BaseModel):
    answered: bool = True


class DomainEntity(BaseModel):
    name: str
    entity_type: str
    description: str


class Relationship(BaseModel):
    source: str
    target: str
    relation: str
    confidence_score: int = Field(ge=0, le=100)


class Decision(BaseModel):
    decision: str
    rationale: str
    confidence_score: int = Field(ge=0, le=100)


class MvpPlan(BaseModel):
    recommended_mvp: str
    architecture: list[str]
    backlog: list[str]
    risks: list[str]


class ProjectReport(BaseModel):
    project_id: UUID = Field(default_factory=uuid4)
    idea: str
    confidence_score: int = Field(ge=0, le=100)
    target_confidence: int
    can_finalize: bool
    domain_map: list[Relationship]
    critical_questions: list[OpenQuestion]
    sources: list[Source]
    competitors: list[str]
    findings: list[Finding]
    hypotheses: list[Hypothesis]
    decisions: list[Decision]
    mvp: MvpPlan
    blockers: list[str]


class ProjectSummary(BaseModel):
    project_id: UUID
    idea: str
    confidence_score: int = Field(ge=0, le=100)
    target_confidence: int
    can_finalize: bool


class ResearchRun(BaseModel):
    id: int
    project_id: UUID
    status: ResearchRunStatus
    objective: str
    planned_questions: list[str] = Field(default_factory=list)
    generated_source_ids: list[int] = Field(default_factory=list)
    generated_finding_ids: list[int] = Field(default_factory=list)
    notes: str = ""


class CreateResearchRunRequest(BaseModel):
    objective: str = Field(min_length=10)
    question_ids: list[int] = Field(default_factory=list)


class UpdateResearchRunRequest(BaseModel):
    status: ResearchRunStatus
    notes: str = ""


class PlannedResearchRun(BaseModel):
    run: ResearchRun
    rationale: str
    targeted_blockers: list[str] = Field(default_factory=list)
