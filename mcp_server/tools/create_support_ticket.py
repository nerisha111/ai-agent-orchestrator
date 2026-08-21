#generates a ticket inside the postgres table and records an assigned event in the interaction table

from typing import Optional
from pydantic import BaseModel, Field
from tools.base import tool
from db import get_db_cursor

class CreateSupportTicket(BaseModel):
    subject: str = Field(..., description="Subject or brief title of the customer support query.")
    description: str = Field(..., description="The complete text detailing the user's issue.")
    priority: Optional[str] = Field("medium", description="Ticket priority: 'low', 'medium', 'high', 'critical'.")
    assigned_to: Optional[str] = Field(None, description="The specific department or agent email to assign the work to.")

@tool(
    name="create_support_ticket",
    description="Creates a customer support ticket and logs the assignment activity details.",
    input_model=CreateSupportTicket,
    risk_level="write"
)
def create_support_ticket(
    subject: str,
    description: str,
    priority: str = "medium",
    assigned_to: Optional[str] = None
) -> dict:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO support_tickets (subject, description, priority, assigned_to)
            VALUES (%s, %s, %s, %s)
            RETURNING id, subject, description, priority, status, assigned_to, created_at;
            """,
            (subject, description, priority, assigned_to)
        )
        ticket = cur.fetchone()
        
       
        ticket["created_at"] = ticket["created_at"].isoformat()

        
        cur.execute(
            "INSERT INTO interactions (entity_type, entity_id, action, details) VALUES ('ticket', %s, 'ticket_created', %s);",
            (ticket["id"], f"Ticket generated with priority level: {priority}")
        )

        return {
            "success": True,
            "ticket": ticket
        }