"""
tool_registry.py
================
LAYER: MCP Tool Registry

Central registry mapping tool names to MCP servers.
Agents discover tools here — no hardcoded server URLs in agent code.
Add new tools here when extending the platform.
"""

from typing import Dict
from app.config import settings

TOOL_REGISTRY: Dict[str, str] = {
    # Banking MCP Server tools
    "get_transaction_history": settings.banking_mcp_url,
    "check_velocity": settings.banking_mcp_url,
    "flag_transaction": settings.banking_mcp_url,
    "freeze_account": settings.banking_mcp_url,
    "get_account_info": settings.banking_mcp_url,
    "get_risk_signals": settings.banking_mcp_url,

    # Compliance MCP Server tools
    "kyc_status": settings.compliance_mcp_url,
    "sanctions_check": settings.compliance_mcp_url,
    "aml_screening": settings.compliance_mcp_url,
    "gdpr_audit_log": settings.compliance_mcp_url,
    "generate_sar_report": settings.compliance_mcp_url,
}


def get_server_for_tool(tool_name: str) -> str:
    """Return the MCP server URL for a given tool name."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: '{tool_name}'. Register it in tool_registry.py")
    return TOOL_REGISTRY[tool_name]


def list_all_tools() -> list:
    """Return all registered tool names."""
    return list(TOOL_REGISTRY.keys())


def list_tools_for_server(server_url: str) -> list:
    """Return all tools registered on a specific MCP server."""
    return [tool for tool, url in TOOL_REGISTRY.items() if url == server_url]
