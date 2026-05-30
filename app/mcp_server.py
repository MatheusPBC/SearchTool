import json
import sys
from collections.abc import Callable
from typing import Any
from uuid import UUID

from app.db import SessionLocal, init_db
from app.services.research_service import ResearchService

Json = dict[str, Any]


def main() -> int:
    init_db()
    for line in sys.stdin:
        if not line.strip():
            continue
        response = _handle_message(json.loads(line))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


def _handle_message(message: Json) -> Json | None:
    method = message.get("method")
    request_id = message.get("id")

    try:
        if method == "initialize":
            return _response(request_id, _initialize_result())
        if method == "tools/list":
            return _response(request_id, {"tools": _tools()})
        if method == "tools/call":
            params = message.get("params") or {}
            return _response(request_id, _call_tool(params))
        if method and method.startswith("notifications/"):
            return None
        return _error(request_id, -32601, f"Method not found: {method}")
    except ValueError as exc:
        return _tool_error(request_id, str(exc))
    except Exception as exc:
        return _error(request_id, -32603, str(exc))


def _initialize_result() -> Json:
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "autonomous-research-mvp",
            "version": "0.1.0",
        },
        "capabilities": {
            "tools": {},
        },
    }


def _call_tool(params: Json) -> Json:
    name = params.get("name")
    arguments = params.get("arguments") or {}

    handler = _tool_handlers().get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")

    with SessionLocal() as db:
        result = handler(ResearchService(db), arguments)

    return _text_content(result)


def _tool_handlers() -> dict[str, Callable[[ResearchService, Json], Any]]:
    return {
        "create_project": lambda service, args: service.create_project(
            idea=_required_str(args, "idea"),
            target_confidence=int(args.get("target_confidence", 85)),
        ),
        "list_projects": lambda service, args: service.list_projects(),
        "show_project": lambda service, args: service.show_project(_uuid(args, "project_id")),
        "list_questions": lambda service, args: service.list_questions(_uuid(args, "project_id")),
        "answer_question": lambda service, args: service.answer_question(
            _uuid(args, "project_id"),
            int(args["question_id"]),
            bool(args.get("answered", True)),
        ),
        "plan_next_run": lambda service, args: service.plan_next_run(_uuid(args, "project_id")),
        "next_action": lambda service, args: service.next_action(_uuid(args, "project_id")),
        "list_runs": lambda service, args: service.list_runs(_uuid(args, "project_id")),
        "create_run": lambda service, args: service.create_run(
            _uuid(args, "project_id"),
            objective=_required_str(args, "objective"),
            question_ids=[int(item) for item in args.get("question_ids", [])],
        ),
        "update_run": lambda service, args: service.update_run(
            _uuid(args, "project_id"),
            int(args["run_id"]),
            status=_required_str(args, "status"),
            notes=str(args.get("notes", "")),
        ),
        "ingest_source": lambda service, args: service.ingest_source(
            _uuid(args, "project_id"),
            title=_required_str(args, "title"),
            source_type=_required_str(args, "source_type"),
            reliability_score=int(args["reliability_score"]),
            notes=_required_str(args, "notes"),
            content=_required_str(args, "content"),
            url=args.get("url"),
            max_findings=int(args.get("max_findings", 5)),
        ),
        "list_findings": lambda service, args: service.list_findings(_uuid(args, "project_id")),
        "create_finding": lambda service, args: service.create_finding(
            _uuid(args, "project_id"),
            statement=_required_str(args, "statement"),
            evidence_level=_required_str(args, "evidence_level"),
            confidence_score=int(args["confidence_score"]),
            source_titles=[str(item) for item in args.get("source_titles", [])],
        ),
        "delete_finding": lambda service, args: service.delete_finding(
            _uuid(args, "project_id"),
            int(args["finding_id"]),
        ),
        "list_hypotheses": lambda service, args: service.list_hypotheses(_uuid(args, "project_id")),
        "update_hypothesis": lambda service, args: service.update_hypothesis(
            _uuid(args, "project_id"),
            int(args["hypothesis_id"]),
            evidence_level=_required_str(args, "evidence_level"),
            confidence_score=int(args["confidence_score"]),
        ),
        "recalculate": lambda service, args: service.recalculate(_uuid(args, "project_id")),
    }


def _tools() -> list[Json]:
    return [
        _tool("create_project", "Create a research project from a vague idea.", {
            "idea": {"type": "string"},
            "target_confidence": {"type": "integer", "default": 85},
        }, ["idea"]),
        _tool("list_projects", "List persisted research projects.", {}, []),
        _tool("show_project", "Return the full persisted project report.", _project_id_schema(), ["project_id"]),
        _tool("list_questions", "List project open questions.", _project_id_schema(), ["project_id"]),
        _tool("answer_question", "Mark a project question answered or unanswered.", {
            **_project_id_schema(),
            "question_id": {"type": "integer"},
            "answered": {"type": "boolean", "default": True},
        }, ["project_id", "question_id"]),
        _tool("plan_next_run", "Plan the next research run.", _project_id_schema(), ["project_id"]),
        _tool("next_action", "Plan and return the recommended next action for an agent.", _project_id_schema(), ["project_id"]),
        _tool("list_runs", "List project research runs.", _project_id_schema(), ["project_id"]),
        _tool("create_run", "Create a manual research run.", {
            **_project_id_schema(),
            "objective": {"type": "string"},
            "question_ids": {"type": "array", "items": {"type": "integer"}},
        }, ["project_id", "objective"]),
        _tool("update_run", "Update research run status.", {
            **_project_id_schema(),
            "run_id": {"type": "integer"},
            "status": {"type": "string", "enum": ["planned", "running", "completed", "blocked"]},
            "notes": {"type": "string"},
        }, ["project_id", "run_id", "status"]),
        _tool("ingest_source", "Persist a source and extract findings from its content.", {
            **_project_id_schema(),
            "title": {"type": "string"},
            "url": {"type": "string"},
            "source_type": {"type": "string"},
            "reliability_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "notes": {"type": "string"},
            "content": {"type": "string"},
            "max_findings": {"type": "integer", "default": 5},
        }, ["project_id", "title", "source_type", "reliability_score", "notes", "content"]),
        _tool("list_findings", "List project findings.", _project_id_schema(), ["project_id"]),
        _tool("create_finding", "Create a finding manually.", {
            **_project_id_schema(),
            "statement": {"type": "string"},
            "evidence_level": {"type": "string", "enum": ["none", "weak", "moderate", "strong"]},
            "confidence_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "source_titles": {"type": "array", "items": {"type": "string"}},
        }, ["project_id", "statement", "evidence_level", "confidence_score"]),
        _tool("delete_finding", "Delete an incorrect or low-quality finding.", {
            **_project_id_schema(),
            "finding_id": {"type": "integer"},
        }, ["project_id", "finding_id"]),
        _tool("list_hypotheses", "List project hypotheses.", _project_id_schema(), ["project_id"]),
        _tool("update_hypothesis", "Update evidence level and confidence for a hypothesis.", {
            **_project_id_schema(),
            "hypothesis_id": {"type": "integer"},
            "evidence_level": {"type": "string", "enum": ["none", "weak", "moderate", "strong"]},
            "confidence_score": {"type": "integer", "minimum": 0, "maximum": 100},
        }, ["project_id", "hypothesis_id", "evidence_level", "confidence_score"]),
        _tool("recalculate", "Recalculate project confidence and blockers.", _project_id_schema(), ["project_id"]),
    ]


def _tool(name: str, description: str, properties: Json, required: list[str]) -> Json:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


def _project_id_schema() -> Json:
    return {"project_id": {"type": "string", "format": "uuid"}}


def _text_content(value: Any) -> Json:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(value, ensure_ascii=False, indent=2),
            }
        ]
    }


def _tool_error(request_id: Any, message: str) -> Json:
    result = {
        "content": [{"type": "text", "text": json.dumps({"error": message}, ensure_ascii=False)}],
        "isError": True,
    }
    return _response(request_id, result)


def _response(request_id: Any, result: Json) -> Json:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> Json:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _uuid(args: Json, key: str) -> UUID:
    return UUID(_required_str(args, key))


def _required_str(args: Json, key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required string: {key}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
