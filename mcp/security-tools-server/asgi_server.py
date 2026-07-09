#!/usr/bin/env python3
"""
Security Tools MCP Server — ASGI/SSE Transport
================================================
Wraps the MCP server to run as an HTTP SSE server on port 3000.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
import mcp.types as types
import json

from tools.contract import CONTRACT_TOOLS
from tools.centralized import CENTRALIZED_TOOLS
from tools.intel import INTEL_TOOLS
from tools.production import PRODUCTION_TOOLS

ALL_TOOLS = CONTRACT_TOOLS + CENTRALIZED_TOOLS + INTEL_TOOLS + PRODUCTION_TOOLS

# --- MCP Server Setup ---

mcp_server = Server("security-tools")

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [types.Tool.model_construct(
        name=t.name, description=t.description, inputSchema=t.inputSchema
    ) for t in ALL_TOOLS]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    result = await _route_tool(name, arguments)
    return [types.TextContent(type="text", text=result)]

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

# --- SSE Transport ---

sse = SseServerTransport("/messages/")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1],
            mcp_server.create_initialization_options()
        )

async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

# --- Health check ---

async def health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "ok",
        "server": "security-tools-mcp",
        "tools": len(ALL_TOOLS),
        "entry_tools": [
            "contract_audit", "centralized_audit", "production_audit"
        ]
    })

# --- Starlette App ---

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Route("/messages/", handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"🚀 Security Tools MCP Server starting on port {port}")
    print(f"   Tools: {len(ALL_TOOLS)} (3 composite entry + 43 atomic)")
    print(f"   Health: http://0.0.0.0:{port}/health")
    print(f"   SSE:    http://0.0.0.0:{port}/sse")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
