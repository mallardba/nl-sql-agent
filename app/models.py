"""
Pydantic Data Models & API Schemas

Data validation and serialization models for API requests and responses.
Provides type safety, automatic validation, and clear API documentation
for all endpoints in the NL-SQL Agent system.

Key Features:
- Request models with automatic validation and type checking
- Response models with structured data serialization
- Optional field handling for flexible API responses
- Type safety with comprehensive type hints
- Automatic API documentation generation
- Data transformation and serialization utilities
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# Request Models (Input)
class AskRequest(BaseModel):
    question: str
    force_heuristic: bool = False


class ExportRequest(BaseModel):
    results: list


# Response Models (Output)
class AskResponse(BaseModel):
    answer_text: str
    sql: str
    rows: List[Dict[str, Any]]
    chart_json: Optional[Dict[str, Any]] = None
