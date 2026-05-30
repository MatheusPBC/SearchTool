from app.agents.source_ingestor import SourceIngestor
from app.config import settings


class FakeCodexClient:
    def complete_json(self, prompt: str, output_schema: dict) -> dict:
        assert "SOURCE:" in prompt
        assert output_schema["type"] == "object"
        return {
            "findings": [
                {
                    "statement": "A API exige backoff quando retorna status 429.",
                    "evidence_level": "strong",
                    "confidence_score": 92,
                }
            ],
            "notes": "Extracao baseada na fonte fornecida.",
        }


def test_source_ingestor_uses_heuristic_by_default() -> None:
    previous_provider = settings.llm_provider
    settings.llm_provider = "heuristic"
    try:
        extraction = SourceIngestor().extract_findings(
            title="Documentacao",
            source_type="documentation",
            content="Conteudo longo o suficiente para gerar um finding conservador.",
            max_findings=3,
        )
    finally:
        settings.llm_provider = previous_provider

    assert extraction.findings == []
    assert "Fallback heuristico" in extraction.notes


def test_source_ingestor_can_use_codex_cli_client() -> None:
    previous_provider = settings.llm_provider
    settings.llm_provider = "codex_cli"
    try:
        extraction = SourceIngestor(codex_client=FakeCodexClient()).extract_findings(
            title="Documentacao",
            source_type="documentation",
            content="Quando a API retorna 429, clientes devem usar backoff exponencial.",
            max_findings=3,
        )
    finally:
        settings.llm_provider = previous_provider

    assert extraction.findings[0].statement == "A API exige backoff quando retorna status 429."
    assert extraction.findings[0].evidence_level == "strong"
    assert extraction.findings[0].confidence_score == 92
