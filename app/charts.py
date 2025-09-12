"""
Chart helpers (extend as needed).
"""

import json
from typing import Any, Dict, List, Optional

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

        # Embed results data as JSON for export functionality
        results_json = json.dumps(rows) if rows else "[]"

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>NL-SQL Agent Results</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .question-section {{
                    background: #e3f2fd;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .question {{
                    font-size: 1.2em;
                    color: #1976d2;
                    margin: 0;
                }}
                .sql-section {{
                    background: #f3e5f5;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .sql-code {{
                    background: #2d3748;
                    color: #e2e8f0;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    overflow-x: auto;
                    white-space: pre-wrap;
                }}
                .results-section {{
                    margin-bottom: 20px;
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    background: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .data-table th, .data-table td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .data-table th {{
                    background-color: #f7fafc;
                    font-weight: 600;
                    color: #2d3748;
                }}
                .data-table tr:hover {{
                    background-color: #f7fafc;
                }}
                .table-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .export-btn {{
                    background: #4299e1;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: background-color 0.2s;
                }}
                .export-btn:hover {{
                    background: #3182ce;
                }}
                .export-btn:active {{
                    background: #2c5282;
                }}
                .chart-container {{
                    margin-top: 20px;
                }}
                .plotly-chart {{
                    min-height: 400px;
                    border: 1px solid #e2e8f0;
                    border-radius: 5px;
                    overflow: visible;
                    position: relative;
                }}
                .plotly-chart .modebar {{
                    top: 10px !important;
                    right: 10px !important;
                    z-index: 1000 !important;
                }}
                h1, h2, h3 {{
                    color: #2d3748;
                    margin-top: 0;
                }}
                .answer-text {{
                    background: #e8f5e8;
                    padding: 15px;
                    border-radius: 5px;
                    color: #2d5a2d;
                    margin-bottom: 20px;
                }}
                .suggestions-container {{
                    margin-top: 30px;
                    display: flex;
                    gap: 20px;
                    flex-wrap: wrap;
                }}
                .suggestions-section, .related-section {{
                    flex: 1;
                    min-width: 300px;
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #007bff;
                }}
                .suggestions-list, .related-list {{
                    list-style: none;
                    padding: 0;
                    margin: 10px 0 0 0;
                }}
                .suggestions-list li, .related-list li {{
                    background: white;
                    margin: 8px 0;
                    padding: 12px;
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 2px solid transparent;
                }}
                .suggestions-list li:hover, .related-list li:hover {{
                    background: #e3f2fd;
                    border-color: #007bff;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }}
                .suggestions-list li:active, .related-list li:active {{
                    transform: translateY(0);
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .loading {{
                    opacity: 0.6;
                    pointer-events: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NL-SQL Agent Results</h1>
                
                <div class="question-section">
                    <h2>Your Question</h2>
                    <p class="question">"{question}"</p>
                </div>
                
                <div class="answer-text">
                    <strong>Answer:</strong> {answer_text}
                </div>
                
                <div class="sql-section">
                    <h2>Generated SQL</h2>
                    <div class="sql-code">{sql}</div>
                </div>
                
                <div class="results-section">
                    {table_html}
                </div>
                
                {chart_html}
                
                {_create_suggestions_section(query_suggestions, related_questions)}
            </div>
            
            <!-- Embedded results data for export -->
            <script>
                window.queryResults = {results_json};
                
                // Make suggestion items clickable
                document.addEventListener('DOMContentLoaded', function() {{
                    const suggestionItems = document.querySelectorAll('.suggestions-list li, .related-list li');
                    
                    suggestionItems.forEach(function(item) {{
                        item.addEventListener('click', function() {{
                            const question = this.textContent.trim();
                            runSuggestionQuery(question);
                        }});
                    }});
                }});
                
                function runSuggestionQuery(question) {{
                    // Add loading state
                    const container = document.querySelector('.container');
                    container.classList.add('loading');
                    
                    // Show loading message
                    const loadingDiv = document.createElement('div');
                    loadingDiv.innerHTML = `
                        <div style="text-align: center; padding: 20px; background: #e3f2fd; border-radius: 8px; margin: 20px 0;">
                            <h3>🔄 Running Query...</h3>
                            <p>"{question}"</p>
                            <div style="margin-top: 10px;">
                                <div style="display: inline-block; width: 20px; height: 20px; border: 3px solid #007bff; border-radius: 50%; border-top-color: transparent; animation: spin 1s linear infinite;"></div>
                            </div>
                        </div>
                    `;
                    container.appendChild(loadingDiv);
                    
                    // Add spin animation
                    const style = document.createElement('style');
                    style.textContent = `
                        @keyframes spin {{
                            0% {{ transform: rotate(0deg); }}
                            100% {{ transform: rotate(360deg); }}
                        }}
                    `;
                    document.head.appendChild(style);
                    
                    // Make API call
                    fetch('/ask-html?question=' + encodeURIComponent(question))
                        .then(response => response.text())
                        .then(html => {{
                            // Replace the entire page content
                            document.open();
                            document.write(html);
                            document.close();
                        }})
                        .catch(error => {{
                            console.error('Error running suggestion query:', error);
                            container.classList.remove('loading');
                            loadingDiv.innerHTML = `
                                <div style="text-align: center; padding: 20px; background: #ffebee; border-radius: 8px; margin: 20px 0; color: #c62828;">
                                    <h3>❌ Error</h3>
                                    <p>Failed to run query: "${{question}}"</p>
                                    <p>Please try again or refresh the page.</p>
                                </div>
                            `;
                        }});
                }}
            </script>
        </body>
        </html>
        """

        print("HTML page created successfully")
        return html

    except Exception as e:
        print(f"Error in create_complete_html_page: {e}")
        # Return a simple error page
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error Generating Page</h1>
            <p>An error occurred: {str(e)}</p>
            <p>Question: {question}</p>
        </body>
        </html>
        """
