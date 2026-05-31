import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def test_mcp_server_lists_tools_and_calls_create_project() -> None:
    tmp_path = Path(f"research-agent-mcp-test-{uuid4()}")
    tmp_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{(tmp_path / 'mcp.db').as_posix()}"
    env["LLM_PROVIDER"] = "heuristic"

    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "create_project",
                "arguments": {
                    "idea": "Quero criar uma ferramenta MCP para pesquisa autonoma",
                },
            },
        },
    ]

    result = subprocess.run(
        [sys.executable, "-m", "app.mcp_server"],
        input="\n".join(json.dumps(message) for message in messages) + "\n",
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]

    assert responses[0]["result"]["serverInfo"]["name"] == "autonomous-research-mvp"
    tool_names = {tool["name"] for tool in responses[1]["result"]["tools"]}
    assert "create_project" in tool_names
    assert "ingest_source" in tool_names
    assert "delete_finding" in tool_names
    assert "advance_workflow" in tool_names

    content = responses[2]["result"]["content"][0]["text"]
    created = json.loads(content)
    assert created["idea"] == "Quero criar uma ferramenta MCP para pesquisa autonoma"
    assert created["can_finalize"] is False
