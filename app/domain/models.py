from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    target_confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    can_finalize: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recommended_mvp: Mapped[str] = mapped_column(Text, nullable=False)

    sources: Mapped[list["SourceModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    findings: Mapped[list["FindingModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    hypotheses: Mapped[list["HypothesisModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    questions: Mapped[list["OpenQuestionModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["RelationshipModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["DecisionModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    competitors: Mapped[list["CompetitorModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    architecture_items: Mapped[list["ArchitectureItemModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    backlog_items: Mapped[list["BacklogItemModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risks: Mapped[list["RiskModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    blockers: Mapped[list["BlockerModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    research_runs: Mapped[list["ResearchRunModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reliability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="sources")


class FindingModel(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False)
    source_titles: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="findings")


class HypothesisModel(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_level: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    falsification_questions: Mapped[str] = mapped_column(Text, nullable=False, default="")

    project: Mapped[ProjectModel] = relationship(back_populates="hypotheses")


class OpenQuestionModel(Base):
    __tablename__ = "open_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    criticality: Mapped[int] = mapped_column(Integer, nullable=False)
    impact_on_mvp: Mapped[str] = mapped_column(Text, nullable=False)
    answered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    project: Mapped[ProjectModel] = relationship(back_populates="questions")


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    relation: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="relationships")


class DecisionModel(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="decisions")


class CompetitorModel(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="competitors")


class ArchitectureItemModel(Base):
    __tablename__ = "architecture_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    item: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="architecture_items")


class BacklogItemModel(Base):
    __tablename__ = "backlog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    item: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="backlog_items")


class RiskModel(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    risk: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="risks")


class BlockerModel(Base):
    __tablename__ = "blockers"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    blocker: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectModel] = relationship(back_populates="blockers")


class ResearchRunModel(Base):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    project: Mapped[ProjectModel] = relationship(back_populates="research_runs")
    questions: Mapped[list["ResearchRunQuestionModel"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    sources: Mapped[list["ResearchRunSourceModel"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    findings: Mapped[list["ResearchRunFindingModel"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ResearchRunQuestionModel(Base):
    __tablename__ = "research_run_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("open_questions.id"), nullable=False)

    run: Mapped[ResearchRunModel] = relationship(back_populates="questions")


class ResearchRunSourceModel(Base):
    __tablename__ = "research_run_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    run: Mapped[ResearchRunModel] = relationship(back_populates="sources")


class ResearchRunFindingModel(Base):
    __tablename__ = "research_run_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False)
    finding_id: Mapped[int] = mapped_column(ForeignKey("findings.id"), nullable=False)

    run: Mapped[ResearchRunModel] = relationship(back_populates="findings")
