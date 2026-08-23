# Autonomous AI Agent Orchestrator

A self-hosted, zero-cost AI automation engine that ingests multi-source customer requests, classifies intent using an LLM, applies real-time confidence arbitration, and executes custom actions using a dynamically discovered Model Context Protocol (MCP) tool registry.

---

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


