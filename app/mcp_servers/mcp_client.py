"""
mcp_client.py
=============
LAYER: MCP Client

HTTP client that agents use to call MCP server tools.
Handles retries, timeouts, structured error responses.
All agents import this — they never call MCP servers directly.
"""

import httpx
import logging
import json
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Lightweight HTTP client for MCP server tool calls.

    Usage:
        client = MCPClient(server_url=settings.banking_mcp_url)
        result = await client.call_tool("get_transaction_history", {"account_id": "ACC-001"})
    """

    def __init__(self, server_url: str, timeout: float = 10.0, max_retries: int = 2):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call a tool on the MCP server.
        Retries up to max_retries on 5xx errors.
        """
        url = f"{self.server_url}/tools/{tool_name}"
        payload = {"arguments": arguments}

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    logger.debug(f"[MCP_CLIENT] {tool_name} -> {json.dumps(result)[:200]}")
                    return result

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500:
                    raise MCPToolError(
                        tool_name=tool_name,
                        message=f"Client error {e.response.status_code}: {e.response.text}"
                    )
                logger.warning(f"[MCP_CLIENT] {tool_name} attempt {attempt+1} failed: {e}")

            except httpx.TimeoutException:
                last_error = TimeoutError(f"MCP tool {tool_name} timed out after {self.timeout}s")
                logger.warning(f"[MCP_CLIENT] {tool_name} timeout on attempt {attempt+1}")

            except Exception as e:
                last_error = e
                logger.warning(f"[MCP_CLIENT] {tool_name} error on attempt {attempt+1}: {e}")

        raise MCPToolError(
            tool_name=tool_name,
            message=f"All {self.max_retries + 1} attempts failed. Last error: {last_error}"
        )

    async def list_tools(self) -> list:
        """Discover all tools registered on the MCP server."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])

    async def health_check(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.server_url}/health")
                return response.status_code == 200
        except Exception:
            return False


class MCPToolError(Exception):
    """Raised when an MCP tool call fails after retries."""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"MCP tool '{tool_name}' failed: {message}")
