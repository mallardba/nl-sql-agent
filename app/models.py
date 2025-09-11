from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# Request Models (Input)
class AskRequest(BaseModel):
    question: str


class ExportRequest(BaseModel):
    results: list


# Response Models (Output)
class AskResponse(BaseModel):
    answer_text: str
    sql: str
    rows: List[Dict[str, Any]]
    chart_json: Optional[Dict[str, Any]] = None
