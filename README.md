# Autonomous AI Agent Orchestrator

A self-hosted AI automation engine that ingests multi-source customer requests, classifies intent using an LLM, applies real-time confidence arbitration, and executes custom actions using a dynamically discovered Model Context Protocol (MCP) tool registry.

---

## Tech Stack 
* Workflow Engine: n8n (Docker)
* MCP Server: Python, FastAPI, Pydantic
* LLM Backends: Groq API
* Database: PostgreSQL(Docker)
* Containerization: Docker Compose

 
## Architecture Overview

```text
  Incoming Webhook
  (Form, Slack, GitHub)
        │
        ▼
   [ n8n Workflow ] ──(Fetches catalog)──► [ FastAPI MCP Server ]
        │                                         │ (Inspects tools/)
        ▼                                         ▼
  [ LLM Routing ] ◄──(Evaluates Schema)─── [ Tool Registry ]
  (Groq/Ollama)
        │
        ├─► [ Confidence Score < 0.70 ] ──► [ Escalate / Log to DB ]
        │
        └─► [ Confidence Score >= 0.70 ] ──► [ Execute tool over REST ]
                                                      │
                                                      ▼
                                           [ Write to Postgres DB ]


```

## Key Features 
* Dynamic Tool Discovery: MCP Server dynamically parses Python decorated functions (`@tool`), auto-generating Pydantic schemas without static list declarations.
* Confidence Arbitration: Incorporates safety thresholds—low-confidence requests (< 0.70) automatically escalate for manual review instead of executing blind actions.
* Self-hosted Stack: Fully containerized via Docker Compose, bridging local model runtime options (Ollama/Groq), n8n workflow engine, and PostgreSQL.


## Quick Start
1. Clone the repository
   ```bash
   git clone git clone [https://github.com/nerisha111/autonomous-ai-orchestrator.git](https://github.com/nerisha111/autonomous-ai-orchestrator.git)
   cd autonomous-ai-orchestrator

   ```
2. Configure environment varaibles
   ```bash
   cp .env.example .env
   # add your GROQ_API_KEY and PostgreSQL credentials to .env
   ```
   
3. Spin up the stack

   ```bash
   docker compose up -d
   ```

  
   
