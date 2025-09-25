"""
Heuristic SQL Generation Patterns

Centralized configuration for keyword-to-generator mappings
used in heuristic SQL fallback generation.
"""

HEURISTIC_PATTERNS = [
    # Revenue/Sales patterns
    {
        "keywords": ["top", "product", "revenue"],
        "generator": "_generate_revenue_query",
    },
    {"keywords": ["top", "product", "sales"], "generator": "_generate_revenue_query"},
    {
        "keywords": ["best", "selling", "product"],
        "generator": "_generate_revenue_query",
    },
    {
        "keywords": ["highest", "revenue", "product"],
        "generator": "_generate_revenue_query",
    },
    # Time-based patterns
    {"keywords": ["sales", "month"], "generator": "_generate_monthly_sales_query"},
    {"keywords": ["monthly", "sales"], "generator": "_generate_monthly_sales_query"},
    {"keywords": ["monthly", "revenue"], "generator": "_generate_monthly_sales_query"},
    {"keywords": ["revenue", "trend"], "generator": "_generate_monthly_sales_query"},
    {
        "keywords": ["quarterly", "quarter"],
        "generator": "_generate_quarterly_sales_query",
    },
    {
        "keywords": ["sales", "quarter"],
        "generator": "_generate_quarterly_sales_query",
    },
    {
        "keywords": ["revenue", "quarter"],
        "generator": "_generate_quarterly_sales_query",
    },
    # Customer patterns
    {"keywords": ["top", "customer"], "generator": "_generate_customer_query"},
    {
        "keywords": ["customer", "order", "value"],
        "generator": "_generate_customer_query",
    },
    {"keywords": ["new", "customer"], "generator": "_generate_new_customer_query"},
    # Product patterns
    {"keywords": ["product", "inventory"], "generator": "_generate_inventory_query"},
    {"keywords": ["low", "stock"], "generator": "_generate_inventory_query"},
    {"keywords": ["product", "category"], "generator": "_generate_category_query"},
    # Order patterns
    {"keywords": ["order", "status"], "generator": "_generate_order_status_query"},
    {"keywords": ["recent", "order"], "generator": "_generate_recent_orders_query"},
]

# Default fallback queries
FALLBACK_QUERIES = {
    "invalid_input": "SELECT 'Invalid question input' AS message, COUNT(*) AS total_orders FROM orders LIMIT 1;",
    "no_match": "SELECT 'No specific pattern matched' AS message, COUNT(*) AS total_orders FROM orders LIMIT 1;",
}
