import os
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .agent import answer_question
from .charts import create_complete_html_page
from .error_logger import get_error_logs, get_error_summary
from .learning import get_learning_metrics
from .models import AskRequest, ExportRequest
from .schema_index import get_embedding_stats, initialize_schema_embeddings
from .tools import export_to_csv, get_schema_metadata

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


@app.get("/errors/logs")
def error_logs(limit: int = 50):
    """Get recent AI error logs."""
    return get_error_logs(limit=limit)


@app.get("/errors/summary")
def error_summary():
    """Get error summary and statistics."""
    return get_error_summary()


@app.get("/learning/dashboard", response_class=HTMLResponse)
def learning_dashboard():
    """Display learning metrics in a clean HTML dashboard."""
    try:
        metrics = get_learning_metrics()

        # Calculate additional derived metrics
        total_queries = metrics.get("total_queries", 0)
        success_rate = metrics.get("success_rate", 0)
        avg_response_time = metrics.get("avg_response_time", 0)

        # Get category performance
        category_performance = metrics.get("category_performance", {})
        category_data = []
        for category, perf in category_performance.items():
            if perf.get("total", 0) > 0:
                category_data.append(
                    {
                        "name": category.replace("_", " ").title(),
                        "total": perf.get("total", 0),
                        "successful": perf.get("successful", 0),
                        "success_rate": perf.get("success_rate", 0),
                    }
                )

        # Sort by total queries
        category_data.sort(key=lambda x: x["total"], reverse=True)

        # Get error patterns
        error_patterns = metrics.get("error_patterns", {})
        error_data = [{"type": k, "count": v} for k, v in error_patterns.items()]
        error_data.sort(key=lambda x: x["count"], reverse=True)

        # Get query complexity
        complexity = metrics.get("query_complexity", {})
        complexity_data = [{"level": k, "count": v} for k, v in complexity.items()]

        # Get accuracy by source
        accuracy_by_source = metrics.get("accuracy_by_source", {})
        source_data = []
        for source, data in accuracy_by_source.items():
            if isinstance(data, dict):
                source_data.append(
                    {
                        "source": source,
                        "successful": data.get("successful", 0),
                        "total": data.get("total", 0),
                        "accuracy_percentage": data.get("accuracy_percentage", "0.0%"),
                    }
                )
            else:
                # Handle old format for backward compatibility
                source_data.append(
                    {
                        "source": source,
                        "successful": data,
                        "total": data,
                        "accuracy_percentage": "100.0%" if data > 0 else "0.0%",
                    }
                )

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NL-SQL Agent - Learning Dashboard</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 700;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 1.1rem;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    padding: 30px;
                }}
                .metric-card {{
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 20px;
                    border-left: 4px solid #4f46e5;
                }}
                .metric-card h3 {{
                    margin: 0 0 10px 0;
                    color: #374151;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .metric-value {{
                    font-size: 2rem;
                    font-weight: 700;
                    color: #1f2937;
                    margin: 0;
                }}
                .metric-subtitle {{
                    color: #6b7280;
                    font-size: 0.9rem;
                    margin: 5px 0 0 0;
                }}
                .section {{
                    margin: 30px;
                }}
                .section h2 {{
                    color: #374151;
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .category-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }}
                .category-item {{
                    background: #f3f4f6;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 3px solid #10b981;
                }}
                .category-name {{
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 5px;
                }}
                .category-stats {{
                    font-size: 0.9rem;
                    color: #6b7280;
                }}
                .success-rate {{
                    color: #059669;
                    font-weight: 600;
                }}
                .error-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                }}
                .error-item {{
                    background: #fef2f2;
                    padding: 10px;
                    border-radius: 6px;
                    border-left: 3px solid #ef4444;
                }}
                .error-type {{
                    font-weight: 600;
                    color: #dc2626;
                }}
                .error-count {{
                    color: #991b1b;
                    font-size: 0.9rem;
                }}
                .chart-container {{
                    background: #f8fafc;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .no-data {{
                    text-align: center;
                    color: #6b7280;
                    font-style: italic;
                    padding: 40px;
                }}
                .refresh-btn {{
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: #4f46e5;
                    color: white;
                    border: none;
                    border-radius: 50px;
                    padding: 15px 20px;
                    cursor: pointer;
                    font-weight: 600;
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
                    transition: all 0.2s;
                }}
                .refresh-btn:hover {{
                    background: #3730a3;
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧠 Learning Dashboard</h1>
                    <p>NL-SQL Agent Performance Metrics</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Total Queries</h3>
                        <p class="metric-value">{total_queries:,}</p>
                        <p class="metric-subtitle">Questions processed</p>
                    </div>
                    <div class="metric-card">
                        <h3>Success Rate</h3>
                        <p class="metric-value">{success_rate:.1%}</p>
                        <p class="metric-subtitle">Successful responses</p>
                    </div>
                    <div class="metric-card">
                        <h3>Avg Response Time</h3>
                        <p class="metric-value">{avg_response_time:.2f}s</p>
                        <p class="metric-subtitle">Seconds per query</p>
                    </div>
                    <div class="metric-card">
                        <h3>AI Usage</h3>
                        <p class="metric-value">{metrics.get('ai_usage_rate', 0):.1%}</p>
                        <p class="metric-subtitle">AI-generated queries</p>
                    </div>
                    <div class="metric-card">
                        <h3>Cache Hit Rate</h3>
                        <p class="metric-value">{metrics.get('cache_hit_rate', 0):.1%}</p>
                        <p class="metric-subtitle">Cached responses</p>
                    </div>
                    <div class="metric-card">
                        <h3>Correction Rate</h3>
                        <p class="metric-value">{metrics.get('correction_rate', 0):.1%}</p>
                        <p class="metric-subtitle">SQL corrections applied</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 Query Categories</h2>
                    <div class="category-list">
                        {''.join([f'''
                        <div class="category-item">
                            <div class="category-name">{cat['name']}</div>
                            <div class="category-stats">
                                {cat['successful']}/{cat['total']} queries
                                <span class="success-rate">({cat['success_rate']:.1%} success)</span>
                            </div>
                        </div>
                        ''' for cat in category_data]) if category_data else '<div class="no-data">No category data available</div>'}
                    </div>
                </div>
                
                <div class="section">
                    <h2>⚠️ Error Patterns</h2>
                    <div class="error-list">
                        {''.join([f'''
                        <div class="error-item">
                            <div class="error-type">{error['type'].replace('_', ' ').title()}</div>
                            <div class="error-count">{error['count']} occurrences</div>
                        </div>
                        ''' for error in error_data]) if error_data else '<div class="no-data">No errors recorded</div>'}
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔍 Query Complexity</h2>
                    <div class="chart-container">
                        {''.join([f'''
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                            <span style="font-weight: 600; color: #374151;">{comp['level'].title()}</span>
                            <span style="color: #6b7280;">{comp['count']} queries</span>
                        </div>
                        ''' for comp in complexity_data]) if complexity_data else '<div class="no-data">No complexity data available</div>'}
                    </div>
                </div>
                
                <div class="section">
                    <h2>🎯 Accuracy by Source</h2>
                    <div class="chart-container">
                        {''.join([f'''
                        <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 6px;">
                            <span style="font-weight: 600; color: #374151;">{source['source'].title()}</span>
                            <div style="text-align: right;">
                                <div style="color: #6b7280; font-size: 0.9rem;">{source['successful']}/{source['total']} queries</div>
                                <div style="color: #059669; font-weight: 600;">{source['accuracy_percentage']} accuracy</div>
                            </div>
                        </div>
                        ''' for source in source_data]) if source_data else '<div class="no-data">No source data available</div>'}
                    </div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="window.location.reload()">
                🔄 Refresh
            </button>
            
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(() => {{
                    window.location.reload();
                }}, 30000);
            </script>
        </body>
        </html>
        """

        return HTMLResponse(
            content=html_content, headers={"Content-Type": "text/html; charset=utf-8"}
        )

    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
                <h1>Error Loading Dashboard</h1>
                <p>Failed to load learning metrics: {str(e)}</p>
                <a href="/learning/metrics" style="color: #4f46e5;">View Raw Metrics</a>
            </body>
            </html>
            """,
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
