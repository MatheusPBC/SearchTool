import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

from app.db import SessionLocal, init_db
from app.domain.schemas import ResearchRunStatus
from app.services.research_service import ResearchService


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    init_db()

    try:
        with SessionLocal() as db:
            result = args.handler(args, ResearchService(db))
    except ValueError as exc:
        _print_error(str(exc))
        return 2

    _print_json(result)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="JSON-first CLI for the Autonomous Research-to-MVP Agent.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-project")
    create.add_argument("--idea", required=True)
    create.add_argument("--target-confidence", type=int, default=85)
    create.set_defaults(handler=_create_project)

    list_cmd = subparsers.add_parser("list-projects")
    list_cmd.set_defaults(handler=_list_projects)

    show = subparsers.add_parser("show-project")
    show.add_argument("project_id")
    show.set_defaults(handler=_show_project)

    plan = subparsers.add_parser("plan-next-run")
    plan.add_argument("project_id")
    plan.set_defaults(handler=_plan_next_run)

    update_run = subparsers.add_parser("update-run")
    update_run.add_argument("project_id")
    update_run.add_argument("run_id", type=int)
    update_run.add_argument("--status", choices=[status.value for status in ResearchRunStatus], required=True)
    update_run.add_argument("--notes", default="")
    update_run.set_defaults(handler=_update_run)

    ingest = subparsers.add_parser("ingest-source")
    ingest.add_argument("project_id")
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--source-type", required=True)
    ingest.add_argument("--reliability-score", type=int, required=True)
    ingest.add_argument("--notes", required=True)
    ingest.add_argument("--url")
    ingest.add_argument("--content")
    ingest.add_argument("--content-file")
    ingest.add_argument("--max-findings", type=int, default=5)
    ingest.set_defaults(handler=_ingest_source)

    finding = subparsers.add_parser("create-finding")
    finding.add_argument("project_id")
    finding.add_argument("--statement", required=True)
    finding.add_argument("--evidence-level", choices=["none", "weak", "moderate", "strong"], required=True)
    finding.add_argument("--confidence-score", type=int, required=True)
    finding.add_argument("--source-title", action="append", dest="source_titles", default=[])
    finding.set_defaults(handler=_create_finding)

    answer = subparsers.add_parser("answer-question")
    answer.add_argument("project_id")
    answer.add_argument("question_id", type=int)
    answer.add_argument("--answered", choices=["true", "false"], default="true")
    answer.set_defaults(handler=_answer_question)

    hypothesis = subparsers.add_parser("update-hypothesis")
    hypothesis.add_argument("project_id")
    hypothesis.add_argument("hypothesis_id", type=int)
    hypothesis.add_argument("--evidence-level", choices=["none", "weak", "moderate", "strong"], required=True)
    hypothesis.add_argument("--confidence-score", type=int, required=True)
    hypothesis.set_defaults(handler=_update_hypothesis)

    delete_finding = subparsers.add_parser("delete-finding")
    delete_finding.add_argument("project_id")
    delete_finding.add_argument("finding_id", type=int)
    delete_finding.set_defaults(handler=_delete_finding)

    recalculate = subparsers.add_parser("recalculate")
    recalculate.add_argument("project_id")
    recalculate.set_defaults(handler=_recalculate)

    next_action = subparsers.add_parser("next-action")
    next_action.add_argument("project_id")
    next_action.set_defaults(handler=_next_action)

    workflow = subparsers.add_parser("advance-workflow")
    workflow.add_argument("project_id")
    workflow.set_defaults(handler=_advance_workflow)

    return parser


def _create_project(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.create_project(args.idea, args.target_confidence)


def _list_projects(args: argparse.Namespace, service: ResearchService) -> list[dict]:
    return service.list_projects()


def _show_project(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.show_project(_parse_uuid(args.project_id))


def _plan_next_run(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.plan_next_run(_parse_uuid(args.project_id))


def _update_run(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.update_run(
        _parse_uuid(args.project_id),
        args.run_id,
        args.status,
        args.notes,
    )


def _ingest_source(args: argparse.Namespace, service: ResearchService) -> dict:
    content = _resolve_content(args.content, args.content_file)
    return service.ingest_source(
        _parse_uuid(args.project_id),
        title=args.title,
        url=args.url,
        source_type=args.source_type,
        reliability_score=args.reliability_score,
        notes=args.notes,
        content=content,
        max_findings=args.max_findings,
    )


def _answer_question(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.answer_question(
        _parse_uuid(args.project_id),
        args.question_id,
        answered=args.answered == "true",
    )


def _create_finding(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.create_finding(
        _parse_uuid(args.project_id),
        statement=args.statement,
        evidence_level=args.evidence_level,
        confidence_score=args.confidence_score,
        source_titles=args.source_titles,
    )


def _update_hypothesis(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.update_hypothesis(
        _parse_uuid(args.project_id),
        args.hypothesis_id,
        evidence_level=args.evidence_level,
        confidence_score=args.confidence_score,
    )


def _delete_finding(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.delete_finding(_parse_uuid(args.project_id), args.finding_id)


def _recalculate(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.recalculate(_parse_uuid(args.project_id))


def _next_action(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.next_action(_parse_uuid(args.project_id))


def _advance_workflow(args: argparse.Namespace, service: ResearchService) -> dict:
    return service.advance_workflow(_parse_uuid(args.project_id))


def _parse_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid UUID: {value}") from exc


def _resolve_content(content: str | None, content_file: str | None) -> str:
    if content and content_file:
        raise ValueError("Use either --content or --content-file, not both")
    if content:
        return content
    if content_file:
        return Path(content_file).read_text(encoding="utf-8")
    raise ValueError("Missing --content or --content-file")


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _print_error(message: str) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
