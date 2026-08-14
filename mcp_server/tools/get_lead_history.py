#this tool allows the llm to inspect previous timeline logs for an existing contact

from pydantic import BaseModel, Field
from tools.base import tool
from db import get_db_cursor


class LeadHistoryInput(BaseModel):
    email: str = Field(..., description="The email address of the lead to lookup history for.")

@tool(
    name="get_lead_history",
    description="Fetches a lead's profile details and previous system interaction timeline.",
    input_model=LeadHistoryInput,
    risk_level="read"
)
def get_lead_history(email: str) -> dict:
    with get_db_cursor() as cur:
       
        cur.execute("SELECT id, name, email, company, status, source, created_at FROM leads WHERE email = %s;", (email,))
        lead = cur.fetchone()

        if not lead:
            return {
                "found": False,
                "message": f"No lead found associated with the email address: {email}"
            }

        
        lead["created_at"] = lead["created_at"].isoformat()

        cur.execute(
            "SELECT id, action, details, created_at FROM interactions WHERE entity_type = 'lead' AND entity_id = %s ORDER BY created_at DESC;",
            (lead["id"],)
        )
        interactions = cur.fetchall()
        
        for idx in range(len(interactions)):
            interactions[idx]["created_at"] = interactions[idx]["created_at"].isoformat()

        return {
            "found": True,
            "lead": lead,
            "history": interactions
        }