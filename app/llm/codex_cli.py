import json
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.config import settings


class CodexCliError(RuntimeError):
    pass


class CodexCliClient:
    def complete_json(self, prompt: str, output_schema: dict[str, Any]) -> dict[str, Any]:
        schema_path = _write_temp_json(output_schema)
        output_path = _empty_temp_file()

        command = [
            *shlex.split(settings.codex_cli_command),
            "exec",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        if settings.codex_cli_model:
            command[2:2] = ["--model", settings.codex_cli_model]

        try:
            result = subprocess.run(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=settings.codex_cli_timeout_seconds,
                check=False,
            )
            if result.returncode != 0:
                raise CodexCliError(result.stderr.strip() or result.stdout.strip())

            raw_output = output_path.read_text(encoding="utf-8")
            return _parse_json(raw_output)
        except subprocess.TimeoutExpired as exc:
            raise CodexCliError("Codex CLI timed out") from exc
        finally:
            schema_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


def _write_temp_json(data: dict[str, Any]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(data, handle)
    return Path(handle.name)


def _empty_temp_file() -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    with handle:
        pass
    return Path(handle.name)


def _parse_json(raw_output: str) -> dict[str, Any]:
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CodexCliError("Codex CLI did not return valid JSON") from exc

    if not isinstance(parsed, dict):
        raise CodexCliError("Codex CLI returned JSON, but not an object")

    return parsed

