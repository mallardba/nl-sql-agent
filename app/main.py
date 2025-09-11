import os
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from .agent import answer_question
from .charts import create_complete_html_page
from .schema_index import get_embedding_stats, initialize_schema_embeddings
from .tools import export_to_csv, get_schema_metadata

# Global debug flag - can be set via environment variable or command line
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(title="NL-SQL Agent", version="0.1.0")


class AskRequest(BaseModel):
    question: str


class ExportRequest(BaseModel):
    results: list


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/schema")
def schema():
    return get_schema_metadata()


@app.get("/embeddings/status")
def embeddings_status():
    """Check status of embeddings system."""
    try:
        stats = get_embedding_stats()
        return {"status": "ok", "embeddings": stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/embeddings/initialize")
def initialize_embeddings():
    """Initialize schema embeddings."""
    try:
        schema_info = get_schema_metadata()
        initialize_schema_embeddings(schema_info)
        return {
            "status": "success",
            "message": "Schema embeddings initialized successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask(
    req: AskRequest,
    html: bool = Query(False, description="Return HTML response instead of JSON"),
):
    try:
        # Validate question before processing
        if not req.question or not isinstance(req.question, str):
            raise HTTPException(
                status_code=400, detail="Question must be a non-empty string"
            )

        result = answer_question(req.question)

        if html:
            # Return HTML response with embedded charts and tables
            try:
                html_content = create_complete_html_page(
                    question=req.question,
                    sql=result.get("sql", ""),
                    rows=result.get("rows", []),
                    chart_data=result.get("chart_json"),
                    answer_text=result.get(
                        "answer_text", "Query executed successfully."
                    ),
                )
                return HTMLResponse(
                    content=html_content,
                    headers={"Content-Type": "text/html; charset=utf-8"},
                )
            except Exception as html_error:
                print(f"HTML generation error: {html_error}")
                # Fallback to JSON if HTML generation fails
                return JSONResponse(result)
        else:
            # Return JSON response (original behavior)
            return JSONResponse(result)

    except Exception as e:
        print(f"General error in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ask-html")
def ask_html(question: str):
    """Simple GET endpoint for testing HTML responses in browser."""
    try:
        # Validate question before processing
        if not question or not isinstance(question, str):
            raise HTTPException(
                status_code=400, detail="Question must be a non-empty string"
            )

        result = answer_question(question)

        html_content = create_complete_html_page(
            question=question,
            sql=result.get("sql", ""),
            rows=result.get("rows", []),
            chart_data=result.get("chart_json"),
            answer_text=result.get("answer_text", "Query executed successfully."),
        )
        return HTMLResponse(
            content=html_content, headers={"Content-Type": "text/html; charset=utf-8"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-html")
def test_html():
    """Test endpoint that generates HTML without database access."""
    sample_data = [
        {"month": "2024-01", "sales": 15000},
        {"month": "2024-02", "sales": 18000},
        {"month": "2024-03", "sales": 22000},
    ]

    html_content = create_complete_html_page(
        question="Show me sample sales data",
        sql="SELECT month, sales FROM sample_sales ORDER BY month;",
        rows=sample_data,
        chart_data=None,
        answer_text="This is a test response without database access.",
    )
    return HTMLResponse(content=html_content)


@app.post("/export/csv")
def export_csv(req: ExportRequest):
    """Export query results as CSV file using provided data."""
    try:
        # Validate results data
        if not req.results or not isinstance(req.results, list):
            raise HTTPException(
                status_code=400, detail="Results data must be a non-empty list"
            )

        # Generate CSV content from provided results
        csv_content = export_to_csv(req.results)

        # Create filename with timestamp
        filename = f"query_results_{int(time.time())}.csv"

        # Return CSV file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        print(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
