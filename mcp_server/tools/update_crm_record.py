#checks if lead exists,handles inserts or updates 
from typing import Optional
from pydantic import BaseModel, Field
from tools.base import tool
from db import get_db_cursor

class UpdateCRMInput(BaseModel):
    email: str = Field(..., description="The email address of the lead.")
    name: Optional[str] = Field(None, description="The name of the lead.")
    company: Optional[str] = Field(None, description="The company domain or name.")
    status: Optional[str] = Field(None, description="The sales pipeline status.")
    source: Optional[str] = Field(None, description="The lead capture source.")

@tool(
    name="update_crm_record",
    description="Updates or creates a CRM profile entry for a lead and logs the event timeline details.",
    input_model=UpdateCRMInput,
    risk_level="write"
)
def update_crm_record(
    email: str,
    name: Optional[str] = None,
    company: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None
) -> dict:
    with get_db_cursor() as cur:
       
        cur.execute("SELECT id FROM leads WHERE email = %s;", (email,))
        is_existing = cur.fetchone() is not None

       
        query = """
            INSERT INTO leads (email, name, company, status, source)
            VALUES (%s, COALESCE(%s, 'Unknown'), COALESCE(%s, 'Unknown'), COALESCE(%s, 'new'), COALESCE(%s, 'direct'))
            ON CONFLICT (email) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, leads.name),
                company = COALESCE(EXCLUDED.company, leads.company),
                status = COALESCE(EXCLUDED.status, leads.status),
                source = COALESCE(EXCLUDED.source, leads.source),
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, name, email, company, status, source, updated_at;
        """
        cur.execute(query, (email, name, company, status, source))
        lead_record = cur.fetchone()

        action_log = "CRM Lead profile updated." if is_existing else "CRM Lead profile initialized."

        
        lead_record["updated_at"] = lead_record["updated_at"].isoformat()

       
        cur.execute(
            "INSERT INTO interactions (entity_type, entity_id, action, details) VALUES ('lead', %s, 'crm_updated', %s);",
            (lead_record["id"], action_log)
        )

        return {
            "success": True,
            "action": "update" if is_existing else "insert",
            "record": lead_record
        }