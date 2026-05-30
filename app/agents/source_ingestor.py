import json
from dataclasses import dataclass

from app.config import settings
from app.domain.schemas import EvidenceLevel, Finding
from app.llm.codex_cli import CodexCliClient, CodexCliError


@dataclass(frozen=True)
class SourceExtraction:
    findings: list[Finding]
    notes: str


class SourceIngestor:
    def __init__(self, codex_client: CodexCliClient | None = None) -> None:
        self.codex_client = codex_client or CodexCliClient()

    def extract_findings(
        self,
        title: str,
        source_type: str,
        content: str,
        max_findings: int,
    ) -> SourceExtraction:
        if settings.llm_provider == "codex_cli":
            try:
                return self._extract_with_codex_cli(title, source_type, content, max_findings)
            except CodexCliError:
                return self._extract_with_heuristics(title, content)

        return self._extract_with_heuristics(title, content)

    def _extract_with_codex_cli(
        self,
        title: str,
        source_type: str,
        content: str,
        max_findings: int,
    ) -> SourceExtraction:
        response = self.codex_client.complete_json(
            prompt=_build_prompt(title, source_type, content, max_findings),
            output_schema=_source_extraction_schema(),
        )

        findings: list[Finding] = []
        for item in response.get("findings", []):
            if not isinstance(item, dict):
                continue

            statement = str(item.get("statement", "")).strip()
            evidence_level = _parse_evidence_level(str(item.get("evidence_level", "")))
            confidence_score = item.get("confidence_score")

            if not statement or evidence_level is None or not isinstance(confidence_score, int):
                continue

            findings.append(
                Finding(
                    statement=statement,
                    evidence_level=evidence_level,
                    source_titles=[title],
                    confidence_score=max(0, min(100, confidence_score)),
                )
            )

        if not findings:
            return self._extract_with_heuristics(title, content)

        return SourceExtraction(
            findings=findings[:max_findings],
            notes=str(response.get("notes", "")).strip()
            or "Findings extraidos pelo Codex CLI a partir do conteudo fornecido.",
        )

    def _extract_with_heuristics(self, title: str, content: str) -> SourceExtraction:
        return SourceExtraction(
            findings=[],
            notes="Fallback heuristico usado; habilite LLM_PROVIDER=codex_cli para extracao semantica.",
        )


def _build_prompt(title: str, source_type: str, content: str, max_findings: int) -> str:
    payload = {
        "title": title,
        "source_type": source_type,
        "max_findings": max_findings,
        "content": content[:20000],
    }

    return (
        "Voce e o Knowledge Extractor de um agente autonomo de pesquisa para MVPs.\n"
        "Extraia apenas findings sustentados pelo conteudo fornecido.\n"
        "Nao invente fatos, URLs, numeros ou entidades que nao estejam no texto.\n"
        "Cada finding deve ser relevante para decidir arquitetura, riscos, perguntas ou MVP.\n"
        "Use evidence_level=strong somente quando o texto sustentar diretamente a afirmacao.\n"
        "Retorne somente JSON valido no schema solicitado.\n\n"
        f"SOURCE:\n{json.dumps(payload, ensure_ascii=True, indent=2)}"
    )


def _source_extraction_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "statement": {"type": "string"},
                        "evidence_level": {
                            "type": "string",
                            "enum": ["none", "weak", "moderate", "strong"],
                        },
                        "confidence_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["statement", "evidence_level", "confidence_score"],
                },
            },
            "notes": {"type": "string"},
        },
        "required": ["findings", "notes"],
    }


def _parse_evidence_level(value: str) -> EvidenceLevel | None:
    try:
        return EvidenceLevel(value)
    except ValueError:
        return None
