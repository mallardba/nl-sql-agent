"""
Query categorization configuration.

Defines categories, keywords, and patterns for intelligent query classification.
Used by the QueryCategorizer to categorize user questions.
"""

from typing import Dict, List

QUERY_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "analytics": {
        "keywords": [
            "trend",
            "analysis",
            "compare",
            "correlation",
            "growth",
            "decline",
            "pattern",
        ],
        "patterns": [
            "over time",
            "year over year",
            "month over month",
            "vs",
            "versus",
        ],
    },
    "reporting": {
        "keywords": [
            "report",
            "summary",
            "overview",
            "dashboard",
            "total",
            "count",
            "sum",
        ],
        "patterns": [
            "how many",
            "what is the total",
            "show me all",
            "list all",
        ],
    },
    "exploration": {
        "keywords": [
            "find",
            "search",
            "discover",
            "explore",
            "what",
            "which",
            "where",
        ],
        "patterns": ["what are", "which products", "find customers", "show me"],
    },
    "revenue": {
        "keywords": [
            "revenue",
            "sales",
            "profit",
            "income",
            "earnings",
            "money",
        ],
        "patterns": [
            "top products by revenue",
            "sales performance",
            "revenue growth",
        ],
    },
    "customer": {
        "keywords": ["customer", "client", "user", "buyer", "purchaser"],
        "patterns": [
            "customer analysis",
            "customer behavior",
            "customer segments",
        ],
    },
    "product": {
        "keywords": ["product", "item", "inventory", "stock", "catalog"],
        "patterns": [
            "product performance",
            "inventory levels",
            "product categories",
        ],
    },
    "time_series": {
        "keywords": [
            "monthly",
            "quarterly",
            "yearly",
            "daily",
            "weekly",
            "trend",
        ],
        "patterns": ["last year", "this quarter", "past 6 months", "over time"],
    },
}
