"""
Query suggestion patterns configuration.

Defines intelligent query suggestions organized by category.
Used by the QueryExpander to provide relevant follow-up questions.
"""

from typing import Dict, List

SUGGESTION_PATTERNS: Dict[str, List[str]] = {
    "revenue": [
        "What are the top products by revenue?",
        "Show me revenue trends over time",
        "Which customers generate the most revenue?",
        "What's our total revenue this quarter?",
    ],
    "customer": [
        "Who are our top customers?",
        "Show me customer segments",
        "What's the average order value by customer?",
        "Which customers haven't ordered recently?",
    ],
    "product": [
        "What are our best-selling products?",
        "Show me product performance by category",
        "Which products need restocking?",
        "What's the inventory level for each product?",
    ],
    "time_series": [
        "Show me sales trends over the last year",
        "What are the monthly sales patterns?",
        "How has revenue changed quarter over quarter?",
        "What are the seasonal trends?",
    ],
}

# General suggestions used when category-specific ones are exhausted
GENERAL_SUGGESTIONS: List[str] = [
    "What are the top 5 products by revenue?",
    "Show me customer distribution by region",
    "What's our total sales this month?",
    "Which products have the highest profit margins?",
]
