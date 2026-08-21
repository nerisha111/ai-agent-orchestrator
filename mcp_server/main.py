# Initializes FastMCP
# Triggers dynamic lookup during ASGI startup
# Registers each discovered tool with the MCP interface
# Exposes a secondary REST endpoint for arbitration logic

from contextlib import asynccontextmanager, AsyncExitStack
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
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


@app.get("/form", response_class=HTMLResponse)
async def serve_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Inbound Gateway</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-xl shadow-md max-w-md w-full">
            <h2 class="text-2xl font-bold mb-2 text-gray-800">Submit Inbound Query</h2>
            <p class="text-sm text-gray-500 mb-6">Your query will be routed and processed by our dynamic AI Orchestrator.</p>
            
            <form id="leadForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-gray-600 uppercase mb-1">Email Address</label>
                    <input type="email" id="sender" required placeholder="name@company.com" class="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-400 focus:outline-none">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-600 uppercase mb-1">How can we help you?</label>
                    <textarea id="text" rows="4" required placeholder="I would like a custom quote... OR My dashboard is broken..." class="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-indigo-400 focus:outline-none"></textarea>
                </div>
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded transition duration-150">
                    Send to Orchestrator
                </button>
            </form>
            
            <div id="feedback" class="mt-4 p-3 rounded text-sm hidden"></div>
        </div>

        <script>
            document.getElementById('leadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const feedback = document.getElementById('feedback');
                feedback.classList.add('hidden');
                
                const payload = {
                    sender: document.getElementById('sender').value,
                    text: document.getElementById('text').value,
                    source: "web_form"
                };

                try {
                    // Points to the production webhook path (/webhook/)
                    // Change to /webhook-test/ if you are clicking "Listen for test event" manually
                    const response = await fetch('http://localhost:5678/webhook/incoming-lead-support', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    const data = await response.json();
                    feedback.className = "mt-4 p-3 rounded text-sm bg-green-50 text-green-700 border border-green-200";
                    feedback.innerText = data.message || "Submitted successfully!";
                    feedback.classList.remove('hidden');
                } catch (err) {
                    feedback.className = "mt-4 p-3 rounded text-sm bg-red-50 text-red-700 border border-red-200";
                    feedback.innerText = "Error transmitting to n8n: " + err.message;
                    feedback.classList.remove('hidden');
                }
            });
        </script>
    </body>
    </html>
    """


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


class ExecutionPayload(BaseModel):
    arguments: dict


@app.post("/tools/{tool_name}/execute")
async def execute_tool_endpoint(tool_name: str, payload: ExecutionPayload):
    if tool_name not in registry.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found in registry.")

    func = registry.tools[tool_name]
    meta = registry.get_tool_metadata(tool_name)

    try:
        validated_args = meta.input_model(**payload.arguments)
        result = func(**validated_args.model_dump())
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Execution error inside tool '{tool_name}': {str(e)}"
        )


app.mount("/mcp", mcp.streamable_http_app())