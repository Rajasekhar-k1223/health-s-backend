from pydantic import BaseModel
from typing import Optional, List

class CopilotQuery(BaseModel):
    patient_id: Optional[int] = None
    intent: str # patient_summary, alert_explain, risk_explain, visit_summary, draft_care_plan, draft_note, chat
    context_id: Optional[int] = None # Used for specific alerts or visits
    query: Optional[str] = None # Custom user query

class CopilotResponse(BaseModel):
    response: str
    sources: List[str] = []
