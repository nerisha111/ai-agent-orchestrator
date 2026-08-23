import inspect
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from registry import registry
from db import get_db_cursor

mcp = FastMCP("Dynamic Orchestrator MCP Backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.discover_tools()
    for name, func in registry.tools.items():
        meta = registry.get_tool_metadata(name)
        mcp.tool(name=meta.name, description=meta.description)(func)
        print(f"Successfully registered tool: {meta.name} [{meta.risk_level}]")
    yield

app = FastAPI(title="AI Orchestrator Engine", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "healthy", "registered_tools_count": len(registry.tools)}

@app.get("/registry/tools")
async def get_registered_tools():
    return {"tools": registry.list_tools()}


class ExecutionPayload(BaseModel):
    arguments: dict

@app.post("/tools/{tool_name}/execute")
async def execute_tool_endpoint(tool_name: str, payload: ExecutionPayload):
    if tool_name not in registry.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

    func = registry.tools[tool_name]
    meta = registry.get_tool_metadata(tool_name)

    try:
        validated_args = meta.input_model(**payload.arguments)
        args_dict = validated_args.model_dump()

        if inspect.iscoroutinefunction(func):
            result = await func(**args_dict)
        else:
            result = func(**args_dict)

        return {"success": True, "tool": tool_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/stats")
def get_stats():
    """Fetches high-level metrics from PostgreSQL."""
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM leads;")
        leads = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) as count FROM support_tickets;")
        tickets = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*), COUNT(CASE WHEN escalated = TRUE THEN 1 END) as esc FROM decision_log;")
        decisions_data = cur.fetchone()
        decisions = decisions_data["count"]
        escalations = decisions_data["esc"] or 0

        return {
            "total_leads": leads,
            "total_tickets": tickets,
            "total_decisions": decisions,
            "total_escalations": escalations
        }

@app.get("/api/decisions")
def get_decisions():
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, trigger_source, classified_intent, confidence_score, routing_action, escalated, created_at
            FROM decision_log
            ORDER BY created_at DESC
            LIMIT 10;
            """
        )
        decisions = cur.fetchall()
        for d in decisions:
            d["created_at"] = d["created_at"].isoformat()
            d["confidence_score"] = float(d["confidence_score"]) if d["confidence_score"] else 0.0
        return decisions

@app.get("/api/leads")
def get_leads():
    with get_db_cursor() as cur:
        cur.execute("SELECT id, name, email, company, status, source, created_at FROM leads ORDER BY created_at DESC LIMIT 5;")
        leads = cur.fetchall()
        for l in leads:
            l["created_at"] = l["created_at"].isoformat()
        return leads

@app.get("/form", response_class=HTMLResponse)
async def serve_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Inbound Gateway</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Sora:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root{
                --rose-950:#2b141d;
                --rose-800:#5c2440;
                --rose-600:#a63466;
                --rose-500:#c94a78;
                --rose-400:#e2739a;
                --rose-200:#f6c9d9;
                --rose-100:#fbe6ee;
                --cream:#fff8f6;
                --gold:#c99a52;
                --ink:#2c1d22;
                --muted:#8a6b75;
            }
            *{box-sizing:border-box;}
            body{
                margin:0;
                min-height:100vh;
                display:flex;
                align-items:center;
                justify-content:center;
                font-family:'Sora',sans-serif;
                background:
                    radial-gradient(circle at 15% 20%, var(--rose-200) 0%, transparent 45%),
                    radial-gradient(circle at 85% 80%, var(--rose-100) 0%, transparent 50%),
                    var(--cream);
                color:var(--ink);
                padding:32px;
                position:relative;
                overflow:hidden;
            }
            body::before{
                content:"";
                position:absolute;
                width:520px;height:520px;
                border-radius:50%;
                background:radial-gradient(circle, rgba(201,74,120,0.16), transparent 70%);
                top:-160px; left:-160px;
            }
            body::after{
                content:"";
                position:absolute;
                width:420px;height:420px;
                border-radius:50%;
                background:radial-gradient(circle, rgba(201,154,82,0.14), transparent 70%);
                bottom:-140px; right:-140px;
            }
            .card{
                position:relative;
                z-index:1;
                max-width:460px;
                width:100%;
                background:#ffffff;
                border-radius:28px;
                padding:44px 40px;
                box-shadow:0 30px 60px -20px rgba(92,36,64,0.25), 0 0 0 1px rgba(201,154,82,0.15);
            }
            .eyebrow{
                font-size:11px;
                letter-spacing:0.22em;
                text-transform:uppercase;
                color:var(--rose-600);
                font-weight:600;
                margin-bottom:10px;
            }
            h2{
                font-family:'Fraunces',serif;
                font-weight:600;
                font-size:30px;
                line-height:1.15;
                margin:0 0 10px;
                color:var(--ink);
            }
            .sub{
                font-size:14px;
                color:var(--muted);
                line-height:1.6;
                margin:0 0 30px;
            }
            form{display:flex;flex-direction:column;gap:20px;}
            label{
                display:block;
                font-size:10.5px;
                font-weight:600;
                letter-spacing:0.14em;
                text-transform:uppercase;
                color:var(--rose-600);
                margin-bottom:8px;
            }
            input, textarea{
                width:100%;
                border:1.5px solid var(--rose-200);
                background:var(--cream);
                border-radius:14px;
                padding:12px 14px;
                font-family:'Sora',sans-serif;
                font-size:14.5px;
                color:var(--ink);
                transition:border-color .2s ease, box-shadow .2s ease;
            }
            input::placeholder, textarea::placeholder{color:#b79aa3;}
            input:focus, textarea:focus{
                outline:none;
                border-color:var(--rose-500);
                box-shadow:0 0 0 4px rgba(201,74,120,0.12);
                background:#fff;
            }
            textarea{resize:vertical;min-height:110px;}
            button{
                margin-top:6px;
                border:none;
                border-radius:14px;
                padding:14px;
                font-family:'Sora',sans-serif;
                font-weight:600;
                font-size:14.5px;
                letter-spacing:0.02em;
                color:#fff;
                cursor:pointer;
                background:linear-gradient(135deg, var(--rose-500), var(--rose-800));
                box-shadow:0 14px 26px -10px rgba(166,52,102,0.55);
                transition:transform .18s ease, box-shadow .18s ease;
            }
            button:hover{transform:translateY(-2px); box-shadow:0 18px 32px -10px rgba(166,52,102,0.65);}
            button:active{transform:translateY(0);}
            #feedback{
                margin-top:22px;
                padding:13px 15px;
                border-radius:12px;
                font-size:13.5px;
                display:none;
                line-height:1.5;
            }
            .feedback-ok{
                display:block;
                background:#f4fbf6;
                color:#2f6b45;
                border:1px solid #cdead4;
            }
            .feedback-err{
                display:block;
                background:#fdf3f4;
                color:#9c3244;
                border:1px solid #f3cdd3;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="eyebrow">Inbound Gateway</div>
            <h2>Send your query<br>to the orchestrator</h2>
            <p class="sub">Every message is read, classified and routed automatically by the dynamic AI orchestrator behind the scenes.</p>
            <form id="leadForm">
                <div>
                    <label for="sender">Email address</label>
                    <input type="email" id="sender" required placeholder="name@company.com">
                </div>
                <div>
                    <label for="text">How can we help you?</label>
                    <textarea id="text" rows="4" required placeholder="I would like a custom quote... OR My dashboard is broken..."></textarea>
                </div>
                <button type="submit">Send to orchestrator</button>
            </form>
            <div id="feedback"></div>
        </div>

        <script>
            document.getElementById('leadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const feedback = document.getElementById('feedback');
                feedback.className = "";
                feedback.style.display = "none";

                const payload = {
                    sender: document.getElementById('sender').value,
                    text: document.getElementById('text').value,
                    source: "web_form"
                };

                try {
                    const response = await fetch('http://localhost:5678/webhook/incoming-lead-support', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    const data = await response.json();
                    feedback.className = "feedback-ok";
                    feedback.innerText = data.message || "Submitted successfully!";
                } catch (err) {
                    feedback.className = "feedback-err";
                    feedback.innerText = "Error transmitting to n8n: " + err.message;
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Orchestrator Dashboard</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root{
                --rose-950:#2b141d;
                --rose-800:#5c2440;
                --rose-600:#a63466;
                --rose-500:#c94a78;
                --rose-400:#e2739a;
                --rose-200:#f6c9d9;
                --rose-100:#fbe6ee;
                --cream:#fff8f6;
                --gold:#c99a52;
                --ink:#2c1d22;
                --muted:#8a6b75;
                --crimson:#c23c54;
                --green:#2f6b45;
                --border:rgba(201,74,120,0.14);
            }
            *{box-sizing:border-box;}
            body{
                margin:0;
                min-height:100vh;
                font-family:'Sora',sans-serif;
                background:
                    radial-gradient(circle at 15% 0%, var(--rose-200) 0%, transparent 45%),
                    radial-gradient(circle at 85% 100%, var(--rose-100) 0%, transparent 50%),
                    var(--cream);
                color:var(--ink);
                position:relative;
                overflow-x:hidden;
            }
            body::before{
                content:"";
                position:fixed;
                width:520px;height:520px;
                border-radius:50%;
                background:radial-gradient(circle, rgba(201,74,120,0.14), transparent 70%);
                top:-180px; left:-160px;
                pointer-events:none;
            }
            body::after{
                content:"";
                position:fixed;
                width:420px;height:420px;
                border-radius:50%;
                background:radial-gradient(circle, rgba(201,154,82,0.12), transparent 70%);
                bottom:-160px; right:-140px;
                pointer-events:none;
            }
            header{
                border-bottom:1px solid var(--border);
                background:rgba(255,248,246,0.85);
                backdrop-filter:blur(10px);
                padding:20px 32px;
                position:sticky;
                top:0;
                z-index:5;
            }
            .header-inner{
                max-width:1280px;
                margin:0 auto;
                display:flex;
                justify-content:space-between;
                align-items:center;
            }
            .brand{
                display:flex;
                align-items:center;
                gap:12px;
            }
            .pulse-dot{
                height:11px;width:11px;
                border-radius:50%;
                background:var(--rose-500);
                box-shadow:0 0 0 0 rgba(201,74,120,0.35);
                animation:pulse 2.2s infinite;
            }
            @keyframes pulse{
                0%{box-shadow:0 0 0 0 rgba(201,74,120,0.35);}
                70%{box-shadow:0 0 0 10px rgba(201,74,120,0);}
                100%{box-shadow:0 0 0 0 rgba(201,74,120,0);}
            }
            h1{
                font-family:'Fraunces',serif;
                font-weight:600;
                font-size:19px;
                letter-spacing:0.01em;
                margin:0;
                color:var(--ink);
            }
            .status-chip{
                font-size:11px;
                letter-spacing:0.08em;
                text-transform:uppercase;
                color:var(--rose-600);
                background:var(--rose-100);
                border:1px solid var(--rose-200);
                padding:6px 14px;
                border-radius:999px;
                font-weight:600;
            }
            main{
                max-width:1280px;
                margin:0 auto;
                padding:36px 32px 60px;
                position:relative;
                z-index:1;
            }
            .stats-grid{
                display:grid;
                grid-template-columns:repeat(4, 1fr);
                gap:18px;
                margin-bottom:28px;
            }
            .stat-card{
                background:#ffffff;
                border:1px solid var(--rose-200);
                border-radius:20px;
                padding:22px 22px 20px;
                position:relative;
                overflow:hidden;
                box-shadow:0 16px 34px -22px rgba(92,36,64,0.25);
            }
            .stat-card::after{
                content:"";
                position:absolute;
                right:-30px; top:-30px;
                width:90px; height:90px;
                border-radius:50%;
                background:radial-gradient(circle, var(--accent, rgba(201,74,120,0.16)), transparent 70%);
                opacity:0.8;
            }
            .stat-label{
                font-size:10.5px;
                font-weight:600;
                letter-spacing:0.14em;
                text-transform:uppercase;
                color:var(--muted);
                margin:0 0 12px;
            }
            .stat-value{
                font-family:'Fraunces',serif;
                font-size:34px;
                font-weight:600;
                margin:0;
                color:var(--ink);
                position:relative;
            }
            .stat-card.leads{--accent:rgba(201,74,120,0.20);}
            .stat-card.leads .stat-value{color:var(--rose-500);}
            .stat-card.tickets{--accent:rgba(201,154,82,0.20);}
            .stat-card.tickets .stat-value{color:var(--gold);}
            .stat-card.decisions .stat-value{color:var(--ink);}
            .stat-card.escalations{--accent:rgba(194,60,84,0.18);}
            .stat-card.escalations .stat-value{color:var(--crimson);}

            .panels-grid{
                display:grid;
                grid-template-columns:2fr 1fr;
                gap:20px;
                align-items:start;
            }
            .panel{
                background:#ffffff;
                border:1px solid var(--rose-200);
                border-radius:24px;
                padding:26px;
                box-shadow:0 20px 44px -28px rgba(92,36,64,0.22);
            }
            .panel h2{
                font-family:'Fraunces',serif;
                font-weight:600;
                font-size:17px;
                margin:0 0 4px;
                color:var(--ink);
            }
            .panel .panel-sub{
                font-size:12px;
                color:var(--muted);
                margin:0 0 18px;
            }
            table{width:100%; border-collapse:collapse;}
            thead th{
                text-align:left;
                font-size:10px;
                font-weight:600;
                letter-spacing:0.12em;
                text-transform:uppercase;
                color:var(--muted);
                padding-bottom:12px;
                border-bottom:1px solid var(--rose-100);
            }
            thead th.center{text-align:center;}
            tbody td{
                padding:13px 6px;
                border-bottom:1px solid var(--rose-100);
                font-size:13px;
                vertical-align:middle;
            }
            tbody tr:hover{background:var(--rose-100);}
            tbody tr:last-child td{border-bottom:none;}
            .mono{font-family:'JetBrains Mono',monospace; font-size:11.5px; color:var(--muted);}
            .badge{
                display:inline-block;
                padding:3px 10px;
                border-radius:999px;
                font-size:11px;
                font-weight:500;
            }
            .badge-lead{background:var(--rose-100); color:var(--rose-600); border:1px solid var(--rose-200);}
            .badge-other{background:#faf1e2; color:var(--gold); border:1px solid #eeddb9;}
            .badge-esc-true{background:#fbe8ea; color:var(--crimson); border:1px solid #f3c9cf;}
            .badge-esc-false{background:#eaf6ee; color:var(--green); border:1px solid #cdead4;}
            .confidence{font-family:'JetBrains Mono',monospace; font-weight:500; color:var(--ink); text-align:center; display:block;}

            .tools-list{list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px;}
            .tool-card{
                background:var(--cream);
                border:1px solid var(--rose-200);
                border-radius:16px;
                padding:14px 16px;
            }
            .tool-top{display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;}
            .tool-name{font-family:'JetBrains Mono',monospace; font-size:12.5px; font-weight:500; color:var(--ink);}
            .tool-desc{font-size:12px; color:var(--muted); line-height:1.5; margin:0;}
            .risk{
                font-size:9.5px;
                letter-spacing:0.06em;
                text-transform:uppercase;
                padding:3px 9px;
                border-radius:999px;
                border:1px solid;
            }
            .risk-read{color:var(--green); border-color:#cdead4; background:#eaf6ee;}
            .risk-write{color:var(--gold); border-color:#eeddb9; background:#faf1e2;}
            .risk-external{color:var(--crimson); border-color:#f3c9cf; background:#fbe8ea;}

            @media (max-width: 900px){
                .stats-grid{grid-template-columns:repeat(2, 1fr);}
                .panels-grid{grid-template-columns:1fr;}
            }
        </style>
    </head>
    <body>
        <header>
            <div class="header-inner">
                <div class="brand">
                    <span class="pulse-dot"></span>
                    <h1>AI Orchestrator Control Panel</h1>
                </div>
                <span class="status-chip">Dynamic MCP Server · Active</span>
            </div>
        </header>

        <main>
            <div class="stats-grid">
                <div class="stat-card leads">
                    <p class="stat-label">Total Leads Captured</p>
                    <p id="stat-leads" class="stat-value">0</p>
                </div>
                <div class="stat-card tickets">
                    <p class="stat-label">Support Tickets</p>
                    <p id="stat-tickets" class="stat-value">0</p>
                </div>
                <div class="stat-card decisions">
                    <p class="stat-label">Processed Decisions</p>
                    <p id="stat-decisions" class="stat-value">0</p>
                </div>
                <div class="stat-card escalations">
                    <p class="stat-label">Escalated Queries</p>
                    <p id="stat-escalations" class="stat-value">0</p>
                </div>
            </div>

            <div class="panels-grid">
                <div class="panel">
                    <h2>Real-Time Decision & Arbitration Logs</h2>
                    <p class="panel-sub">Latest routing decisions made by the orchestrator</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Source</th>
                                <th>Intent</th>
                                <th class="center">Confidence</th>
                                <th>Action</th>
                                <th>Escalated</th>
                            </tr>
                        </thead>
                        <tbody id="decision-table-body"></tbody>
                    </table>
                </div>

                <div class="panel">
                    <h2>Dynamic MCP Tool Catalog</h2>
                    <p class="panel-sub">Exposed at runtime by inspecting the tools/ directory</p>
                    <ul id="tools-list" class="tools-list"></ul>
                </div>
            </div>
        </main>

        <script>
            async function refreshDashboard() {
                try {
                    const statsRes = await fetch('/api/stats');
                    const stats = await statsRes.json();
                    document.getElementById('stat-leads').innerText = stats.total_leads;
                    document.getElementById('stat-tickets').innerText = stats.total_tickets;
                    document.getElementById('stat-decisions').innerText = stats.total_decisions;
                    document.getElementById('stat-escalations').innerText = stats.total_escalations;

                    const decisionsRes = await fetch('/api/decisions');
                    const decisions = await decisionsRes.json();
                    const tbody = document.getElementById('decision-table-body');
                    tbody.innerHTML = '';

                    decisions.forEach(d => {
                        const row = document.createElement('tr');

                        const badgeClass = d.classified_intent === 'lead' ? 'badge badge-lead' : 'badge badge-other';
                        const escBadge = d.escalated
                            ? '<span class="badge badge-esc-true">True</span>'
                            : '<span class="badge badge-esc-false">False</span>';

                        row.innerHTML = `
                            <td class="mono">${d.trigger_source}</td>
                            <td><span class="${badgeClass}">${d.classified_intent}</span></td>
                            <td><span class="confidence">${(d.confidence_score * 100).toFixed(0)}%</span></td>
                            <td class="mono">${d.routing_action}</td>
                            <td>${escBadge}</td>
                        `;
                        tbody.appendChild(row);
                    });

                    const toolsRes = await fetch('/registry/tools');
                    const toolsData = await toolsRes.json();
                    const toolsList = document.getElementById('tools-list');
                    toolsList.innerHTML = '';

                    toolsData.tools.forEach(t => {
                        const li = document.createElement('li');
                        li.className = "tool-card";

                        let riskClass = 'risk risk-read';
                        if (t.risk_level === 'write') riskClass = 'risk risk-write';
                        if (t.risk_level === 'external') riskClass = 'risk risk-external';

                        li.innerHTML = `
                            <div class="tool-top">
                                <span class="tool-name">${t.name}</span>
                                <span class="${riskClass}">${t.risk_level}</span>
                            </div>
                            <p class="tool-desc">${t.description}</p>
                        `;
                        toolsList.appendChild(li);
                    });

                } catch (err) {
                    console.error("Dashboard failed to retrieve real-time data metrics: ", err);
                }
            }

            setInterval(refreshDashboard, 4500);
            window.onload = refreshDashboard;
        </script>
    </body>
    </html>
    """