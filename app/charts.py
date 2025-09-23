"""
Interactive Data Visualization System

Comprehensive chart generation and HTML page creation using Plotly.
Provides intelligent chart type selection, responsive design, and
professional data presentation with interactive features.

Key Features:
- Intelligent chart type detection (bar, line, pie, scatter, area)
- Interactive Plotly charts with hover, zoom, and export capabilities
- Responsive HTML page generation with modern CSS styling
- Data-driven chart configuration and axis optimization
- Professional table formatting with sorting and styling
- Export functionality integration (CSV download)
- Mobile-friendly responsive design
- Query suggestions and related questions integration
"""

import json
from typing import Any, Dict, List, Optional

from .templates import format_query_results_template

# Using Plotly directly in tools.render_chart for MVP.
# Keep this file for future custom specs and formatting.


def create_html_table(
    rows: List[Dict[str, Any]], title: str = "Query Results", question: str = ""
) -> str:
    """Convert SQL results to an HTML table."""
    if not rows or len(rows) == 0:
        return f"<h3>{title}</h3><p>No results found.</p>"

    # Get column headers from first row
    headers = list(rows[0].keys())

    # Start building HTML
    html = f"""
    <div class="table-container">
        <div class="table-header">
            <h3>{title}</h3>
            <button class="export-btn" onclick="exportToCSV()" title="Export to CSV">
                📊 Export CSV
            </button>
        </div>
        <table class="data-table">
            <thead>
                <tr>
    """

    # Add header row
    for header in headers:
        html += f"<th>{header}</th>"

    html += """
                </tr>
            </thead>
            <tbody>
    """

    # Add data rows
    for row in rows:
        html += "<tr>"
        for value in row.values():
            # Format the value nicely
            if value is None:
                html += "<td>NULL</td>"
            elif isinstance(value, (int, float)):
                html += (
                    f"<td>{value:,.2f}</td>"
                    if isinstance(value, float)
                    else f"<td>{value:,}</td>"
                )
            else:
                html += f"<td>{str(value)}</td>"
        html += "</tr>"

    html += """
            </tbody>
        </table>
    </div>
    
    <script>
        function exportToCSV() {
            // Use embedded results data instead of re-querying
            const results = window.queryResults || [];
            
            if (results.length === 0) {
                alert('No data to export');
                return;
            }
            
            // Send results data to export endpoint
            console.log('Starting export with data:', results);
            
            fetch('/export/csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ results: results })
            })
            .then(response => {
                console.log('Export response status:', response.status);
                console.log('Export response headers:', response.headers);
                
                if (!response.ok) {
                    return response.text().then(text => {
                        console.error('Export error response:', text);
                        throw new Error(`Export failed: ${response.status} - ${text}`);
                    });
                }
                return response.blob();
            })
            .then(blob => {
                console.log('Export blob received:', blob.size, 'bytes');
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'query_results.csv';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                console.log('Export download initiated');
            })
            .catch(error => {
                console.error('Export error:', error);
                alert('Export failed: ' + error.message);
            });
        }
    </script>
    """

    return html


def create_html_chart(chart_data: Dict[str, Any], title: str = "Chart") -> str:
    """Convert Plotly chart data to HTML with embedded JavaScript."""
    if not chart_data:
        return f"<h3>{title}</h3><p>No chart data available.</p>"

    # Extract the chart data and layout
    chart_json = json.dumps(chart_data)

    html = f"""
    <div class="chart-container">
        <h3>{title}</h3>
        <div id="chart-{hash(title)}" class="plotly-chart"></div>
        <script>
            Plotly.newPlot('chart-{hash(title)}', {chart_json}.data, {chart_json}.layout, {{
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToAdd: ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
                modeBarButtonsToRemove: [],
                displaylogo: false,
                toImageButtonOptions: {{
                    format: 'png',
                    filename: 'chart',
                    height: 500,
                    width: 700,
                    scale: 1
                }}
            }});
        </script>
    </div>
    """

    return html


def _create_suggestions_section(
    query_suggestions: Optional[List[str]], related_questions: Optional[List[str]]
) -> str:
    """Create HTML section for query suggestions and related questions."""
    if not query_suggestions and not related_questions:
        return ""

    suggestions_html = ""
    if query_suggestions:
        suggestions_list = "".join(
            [f"<li>{suggestion}</li>" for suggestion in query_suggestions]
        )
        suggestions_html = f"""
        <div class="suggestions-section">
            <h3>💡 Query Suggestions</h3>
            <ul class="suggestions-list">
                {suggestions_list}
            </ul>
        </div>
        """

    related_html = ""
    if related_questions:
        related_list = "".join(
            [f"<li>{question}</li>" for question in related_questions]
        )
        related_html = f"""
        <div class="related-section">
            <h3>🔗 Related Questions</h3>
            <ul class="related-list">
                {related_list}
            </ul>
        </div>
        """

    return f"""
    <div class="suggestions-container">
        {suggestions_html}
        {related_html}
    </div>
    """


def create_complete_html_page(
    question: str,
    sql: str,
    rows: List[Dict[str, Any]],
    chart_data: Optional[Dict[str, Any]] = None,
    answer_text: str = "Query executed successfully.",
    query_suggestions: Optional[List[str]] = None,
    related_questions: Optional[List[str]] = None,
) -> str:
    """Create a complete HTML page with question, SQL, results, and chart."""

    try:
        # Debug logging
        print(f"Creating HTML page for question: {question}")
        print(f"SQL: {sql}")
        print(f"Rows count: {len(rows)}")
        print(f"Chart data: {chart_data is not None}")

        # Safely handle chart data
        chart_html = ""
        if chart_data:
            try:
                chart_html = create_html_chart(chart_data, "Data Visualization")
            except Exception as chart_error:
                print(f"Chart generation error: {chart_error}")
                chart_html = "<p>Chart could not be generated.</p>"

        # Safely handle table data
        table_html = ""
        try:
            table_html = create_html_table(rows, "Query Results", question)
        except Exception as table_error:
            print(f"Table generation error: {table_error}")
            table_html = "<p>Table could not be generated.</p>"

        # Create suggestions HTML
        suggestions_html = _create_suggestions_section(
            query_suggestions, related_questions
        )

        # Use template to generate HTML
        html_content = format_query_results_template(
            question=question,
            sql=sql,
            answer_text=answer_text,
            table_html=table_html,
            chart_html=chart_html,
            suggestions_html=suggestions_html,
            rows=rows,
        )

        print("HTML page created successfully")
        return html_content

    except Exception as e:
        print(f"Error in create_complete_html_page: {e}")
        # Return a simple error page using template
        from .templates import format_error_page_template

        return format_error_page_template(
            error_title="Error Generating Page",
            error_message=f"An error occurred: {str(e)}<br>Question: {question}",
            back_url="/",
        )
