"""
rest_app.py
===========
LAYER: MCP Server transport

Exposes a FastMCP server's registered tools over the simple REST contract
that MCPClient (app/mcp_servers/mcp_client.py) speaks:

  GET  /health              -> {"status": "ok", "server": <name>}
  GET  /tools               -> {"tools": [{name, description, input_schema}, ...]}
  POST /tools/{tool_name}   -> body {"arguments": {...}} -> tool result (JSON)
"""

import inspect
import logging

from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    arguments: dict = {}


def build_rest_app(mcp: FastMCP) -> FastAPI:
    app = FastAPI(title=mcp.name)
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}

    @app.get("/health")
    async def health():
        return {"status": "ok", "server": mcp.name, "tools": len(tools)}

    @app.get("/tools")
    async def list_tools():
        return {
            "tools": [
                {"name": t.name, "description": t.description, "input_schema": t.parameters}
                for t in tools.values()
            ]
        }

    @app.post("/tools/{tool_name}")
    async def call_tool(tool_name: str, call: ToolCall):
        tool = tools.get(tool_name)
        if tool is None:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
        try:
            args = tool.fn_metadata.arg_model.model_validate(call.arguments)
            kwargs = args.model_dump_one_level()
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors(include_url=False))
        result = tool.fn(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    return app


def run_rest(mcp: FastMCP, port: int) -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(build_rest_app(mcp), host="0.0.0.0", port=port)
