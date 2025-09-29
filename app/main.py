"""
FastAPI Web Application & API Endpoints

Main FastAPI application providing RESTful API endpoints for the NL-SQL Agent.
Features comprehensive API routes, HTML visualization, learning dashboard,
and error management with professional web interface.

Key Features:
- RESTful API endpoints for natural language to SQL conversion
- Interactive HTML responses with embedded charts and tables
- Learning metrics dashboard with real-time analytics
- Error logging and management endpoints
- Schema metadata and embeddings management
- CSV export functionality with client-side processing
- Health checks and system status monitoring
- Professional web interface with responsive design
- Comprehensive error handling and validation
"""

import os
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .agent import answer_question
from .data import (
    export_to_csv,
    get_embedding_stats,
    get_schema_metadata,
    initialize_schema_embeddings,
)
from .learning import (
    clear_learning_metrics,
    get_learning_metrics,
    process_dashboard_data,
)
from .models import AskRequest, ExportRequest
from .ui import (
    create_complete_html_page,
    format_error_page_template,
    format_learning_dashboard_template,
)
from .utils import clear_error_logs, get_error_logs, get_error_summary, get_log_stats

# Global debug flag - can be set via environment variable or command line
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(title="NL-SQL Agent", version="0.1.0")


@app.get("/health")
def health():
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


@app.get("/learning/metrics")
def learning_metrics():
    """Get learning metrics and performance statistics."""
    return get_learning_metrics()


@app.post("/learning/clear")
def clear_metrics():
    """Clear all learning metrics (useful for testing)."""
    clear_learning_metrics()
    return {"message": "Learning metrics cleared successfully"}


@app.get("/errors/logs")
def error_logs(limit: int = 50):
    """Get recent AI error logs."""
    return get_error_logs(limit=limit)


@app.get("/errors/summary")
def error_summary():
    """Get error summary and statistics."""
    return get_error_summary()


@app.get("/errors/stats")
def get_errors_stats():
    """Get log file statistics."""
    return get_log_stats()


@app.post("/errors/clear")
def clear_errors():
    """Clear all error logs (use with caution)."""
    clear_error_logs()
    return {"message": "Error logs cleared successfully"}


@app.get("/learning/dashboard", response_class=HTMLResponse)
def learning_dashboard():
    """Display learning metrics in a clean HTML dashboard."""
    try:
        metrics = get_learning_metrics()
        dashboard_data = process_dashboard_data(metrics)

        html_content = format_learning_dashboard_template(**dashboard_data)

        return HTMLResponse(
            content=html_content, headers={"Content-Type": "text/html; charset=utf-8"}
        )

    except Exception as e:
        return HTMLResponse(
            content=format_error_page_template(
                error_title="Error Loading Dashboard",
                error_message=f"Failed to load learning metrics: {str(e)}",
                back_url="/learning/metrics",
            ),
            status_code=500,
        )


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
        # Enhanced validation
        if not req.question:
            raise HTTPException(
                status_code=400, detail="Question cannot be empty or None"
            )
        if not isinstance(req.question, str):
            raise HTTPException(
                status_code=400,
                detail=f"Question must be a string, got {type(req.question).__name__}",
            )
        if not req.question.strip():
            raise HTTPException(
                status_code=400, detail="Question cannot be empty or whitespace only"
            )

        result = answer_question(req.question, force_heuristic=req.force_heuristic)

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
                    query_suggestions=result.get("query_suggestions"),
                    related_questions=result.get("related_questions"),
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
def ask_html(question: str, force_heuristic: bool = Query(False)):
    """Simple GET endpoint for testing HTML responses in browser."""
    try:
        # Validate question before processing
        # Enhanced validation
        if not question:
            raise HTTPException(
                status_code=400, detail="Question cannot be empty or None"
            )
        if not question.strip():
            raise HTTPException(
                status_code=400, detail="Question cannot be empty or whitespace only"
            )

        result = answer_question(question, force_heuristic=force_heuristic)

        html_content = create_complete_html_page(
            question=question,
            sql=result.get("sql", ""),
            rows=result.get("rows", []),
            chart_data=result.get("chart_json"),
            answer_text=result.get("answer_text", "Query executed successfully."),
            query_suggestions=result.get("query_suggestions"),
            related_questions=result.get("related_questions"),
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
