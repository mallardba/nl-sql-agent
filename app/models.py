from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class AskResponse(BaseModel):
    answer_text: str
    sql: str
    rows: List[Dict[str, Any]]
    chart_json: Optional[Dict[str, Any]] = None
