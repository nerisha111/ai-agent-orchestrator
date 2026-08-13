# Initializes FastMCP
# Triggers dynamic lookup during ASGI startup
# Registers each discovered tool with the MCP interface
# Exposes a secondary REST endpoint for arbitration logic

from contextlib import asynccontextmanager, AsyncExitStack

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from registry import registry


mcp = FastMCP(
    "Dynamic Orchestrator MCP Backend",
    stateless_http=True
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.discover_tools()

    for name, func in registry.tools.items():
        meta = registry.get_tool_metadata(name)

        mcp.tool(
            name=meta.name,
            description=meta.description
        )(func)

        print(
            f"Successfully registered tool: "
            f"{meta.name} [{meta.risk_level}]"
        )

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(
            mcp.session_manager.run()
        )
        yield


app = FastAPI(
    title="AI Orchestrator Engine",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "registered_tools_count": len(registry.tools)
    }


@app.get("/registry/tools")
async def get_registered_tools():
    return {
        "tools": registry.list_tools()
    }


app.mount("/mcp", mcp.streamable_http_app())