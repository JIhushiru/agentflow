from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from backend.tools.registry import Tool, tool_registry


class ExecutePythonTool(Tool):
    name = "execute_python"
    description = "Execute a Python code snippet in a sandboxed subprocess and return stdout/stderr."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 30).",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    async def execute(self, *, code: str, timeout: int = 30) -> str:
        logger.info(f"Executing Python code ({len(code)} chars)")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
        ) as f:
            f.write(code)
            script_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "python",
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            result = {
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[:4000],
                "stderr": stderr.decode(errors="replace")[:2000],
            }
            return json.dumps(result, indent=2)
        except asyncio.TimeoutError:
            proc.kill()
            return json.dumps({"error": "Execution timed out", "timeout": timeout})
        finally:
            Path(script_path).unlink(missing_ok=True)


# Auto-register
tool_registry.register(ExecutePythonTool())
