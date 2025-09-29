"""
User interface and presentation modules.

This package contains modules for chart generation, HTML templates,
and user interface components.
"""

from .charts import create_complete_html_page
from .templates import (
    format_error_page_template,
    format_learning_dashboard_template,
    format_query_results_template,
)

__all__ = [
    "format_query_results_template",
    "format_learning_dashboard_template",
    "format_error_page_template",
    "create_complete_html_page",
]
