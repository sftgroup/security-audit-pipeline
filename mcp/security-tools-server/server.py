#!/usr/bin/env python3
"""
Security Tools MCP Server — MCP 1.28 compatible
================================================
3 composite entry tools + 43 atomic tools:
  contract_audit     — smart contract security audit
  centralized_audit  — centralized app security audit
  production_audit   — post-deployment security audit
  + 6 intel tools

Agent calls 3 composite tools via MCP stdio.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from tools.contract import CONTRACT_TOOLS
from tools.centralized import CENTRALIZED_TOOLS
from tools.intel import INTEL_TOOLS
from tools.production import PRODUCTION_TOOLS

ALL_TOOLS = CONTRACT_TOOLS + CENTRALIZED_TOOLS + INTEL_TOOLS + PRODUCTION_TOOLS

# Convert Tool objects to dicts for MCP 1.28 compatibility
def _tool_to_dict(t):
    return {
        "name": t.name, "description": t.description,
        "inputSchema": t.inputSchema
    }

async def main():
    server = Server("security-tools")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [types.Tool.model_construct(
            name=t.name, description=t.description, inputSchema=t.inputSchema
        ) for t in ALL_TOOLS]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        result = await _route_tool(name, arguments)
        return [types.TextContent(type="text", text=result)]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

async def _route_tool(name: str, args: dict) -> str:
    from tools.contract import handle_contract_tool
    from tools.centralized import handle_centralized_tool
    from tools.intel import handle_intel_tool
    from tools.production import handle_production_tool

    for handler in [handle_contract_tool, handle_centralized_tool,
                    handle_intel_tool, handle_production_tool]:
        result = await handler(name, args)
        if result is not None:
            return result
    return json.dumps({"error": f"Unknown tool: {name}"})

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
