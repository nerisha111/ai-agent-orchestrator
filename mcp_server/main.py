# a minimal server setup to allow the container to build and complete its healthcheck

import uvicorn
from fastapi import FastAPI

app= FastAPI(title = "Dynamic MCP Server Stub")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service":"mcp_server"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port = 8000, reload=True)
    
