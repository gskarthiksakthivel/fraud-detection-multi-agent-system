# MCP Integration Guide — For Platform Teams

## What is MCP?

Model Context Protocol (MCP) is a standard for exposing tools and resources to AI agents.
In this system, MCP servers are domain microservices that wrap banking/compliance APIs.

## How Agents Call MCP Tools

1. Agent imports `MCPClient`
2. Agent calls `await mcp.call_tool("tool_name", {arguments})`
3. `MCPClient` looks up server URL via `tool_registry.py`
4. HTTP POST to `{server_url}/tools/{tool_name}`
5. Response is a structured dict matching the tool's output schema

```python
from app.mcp_servers.mcp_client import MCPClient
from app.config import settings

mcp = MCPClient(server_url=settings.banking_mcp_url)
result = await mcp.call_tool("get_transaction_history", {
    "account_id": "ACC-001",
    "hours": 24
})
```

## How to Add a New Tool

### Step 1: Add the tool to the MCP server

```python
# In banking_mcp_server.py or compliance_mcp_server.py
@mcp.tool()
async def my_new_tool(param1: str, param2: int) -> dict:
    """Tool description — agents see this."""
    return {"result": "value"}
```

### Step 2: Register in tool_registry.py

```python
# In tool_registry.py
TOOL_REGISTRY = {
    ...
    "my_new_tool": settings.banking_mcp_url,  # or compliance_mcp_url
}
```

### Step 3: Add to the MCP schema JSON

Update `app/mcp_servers/schemas/banking_tools_schema.json` with the tool's input/output schema.

### Step 4: Add contract test

```python
# In tests/contract/test_banking_mcp_contract.py
async def test_my_new_tool_contract():
    result = await mcp.call_tool("my_new_tool", {"param1": "test", "param2": 1})
    assert "result" in result
```

### Step 5: Update agent_cards.json

Add the new tool to the relevant agent's `tools_used` list.

## Tool Naming Conventions

- Use `snake_case`
- Verb_noun pattern: `get_account_info`, `check_velocity`, `flag_transaction`
- Prefix with domain if ambiguous: `banking_get_...` or `compliance_check_...`

## Error Handling

- Tool calls that fail are non-fatal by default — agents log and continue
- 5xx errors are retried up to `max_retries` times (default: 2)
- 4xx errors fail immediately (bad input — no retry)
- All failures are logged via `audit_logger.log_mcp_call()`

## Versioning

- MCP server version is in `mcp_server_version` field of the schema JSON
- Breaking schema changes require a new endpoint version
- Non-breaking additions (new optional fields) are backwards compatible
