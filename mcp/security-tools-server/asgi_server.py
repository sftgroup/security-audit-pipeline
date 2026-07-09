#!/usr/bin/env python3
"""
Security Tools MCP Server — ASGI/SSE + REST Transport
=======================================================
Wraps the MCP server to run as an HTTP SSE server on port 3000.
Also exposes a simple REST API endpoint for sub-agents.
"""

import sys, os
os.environ['PATH'] = os.path.expanduser('~/.foundry/bin:~/.local/bin:/usr/local/bin:/usr/bin:/bin:' + os.environ.get('PATH', ''))
os.environ["PATH"] = os.path.expanduser("~/.foundry/bin:~/.local/bin:/usr/local/bin:" + os.environ.get("PATH", ""))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request
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
    return JSONResponse({
        "status": "ok",
        "server": "security-tools-mcp",
        "tools": len(ALL_TOOLS),
        "entry_tools": [
            "contract_audit", "centralized_audit", "production_audit"
        ]
    })

# --- REST API (for sub-agents — no SSE needed) ---

async def api_call_tool(request: Request):
    """
    Simple REST endpoint: POST /api/tools/{tool_name}
    Body: JSON arguments
    Response: tool output as JSON
    """
    tool_name = request.path_params.get("tool_name", "")
    if not tool_name:
        return JSONResponse({"error": "Missing tool name"}, status_code=400)

    try:
        body = await request.json()
    except Exception:
        body = {}

    try:
        result = await _route_tool(tool_name, body)
        return JSONResponse(json.loads(result) if isinstance(result, str) else result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def api_list_tools(request):
    """GET /api/tools — list all tools"""
    return JSONResponse({
        "tools": [
            {"name": t.name, "description": t.description[:120] + "..." if len(t.description) > 120 else t.description}
            for t in ALL_TOOLS
        ],
        "entry_tools": ["contract_audit", "centralized_audit", "production_audit"],
        "usage": "POST /api/tools/{tool_name} with JSON body"
    })

# --- Starlette App ---

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Route("/messages/", handle_messages, methods=["POST"]),
        Route("/api/tools", api_list_tools, methods=["GET"]),
        Route("/api/tools/{tool_name:str}", api_call_tool, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Security Tools MCP Server starting on port {port}")
    print(f"   Tools: {len(ALL_TOOLS)} (3 composite entry + 43 atomic)")
    print(f"   Health:     GET /health")
    print(f"   SSE:        GET /sse")
    print(f"   REST:       POST /api/tools/{{tool_name}}")
    print(f"   Tool List:  GET /api/tools")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
