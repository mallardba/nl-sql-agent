"""
Chart helpers (extend as needed).
"""

import json
from typing import Any, Dict, List, Optional

# Using Plotly directly in tools.render_chart for MVP.
# Keep this file for future custom specs and formatting.


def create_html_table(rows: List[Dict[str, Any]], title: str = "Query Results") -> str:
    """Convert SQL results to an HTML table."""
    if not rows or len(rows) == 0:
        return f"<h3>{title}</h3><p>No results found.</p>"

    # Get column headers from first row
    headers = list(rows[0].keys())

    # Start building HTML
    html = f"""
    <div class="table-container">
        <h3>{title}</h3>
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
                displayModeBar: true
            }});
        </script>
    </div>
    """

    return html


def create_complete_html_page(
    question: str,
    sql: str,
    rows: List[Dict[str, Any]],
    chart_data: Optional[Dict[str, Any]] = None,
    answer_text: str = "Query executed successfully.",
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
            table_html = create_html_table(rows, "Query Results")
        except Exception as table_error:
            print(f"Table generation error: {table_error}")
            table_html = "<p>Table could not be generated.</p>"

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
                .chart-container {{
                    margin-top: 20px;
                }}
                .plotly-chart {{
                    min-height: 400px;
                    border: 1px solid #e2e8f0;
                    border-radius: 5px;
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
            </div>
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
