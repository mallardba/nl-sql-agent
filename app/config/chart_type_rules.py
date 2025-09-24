"""
Chart Type Determination Rules

Centralized configuration for chart type selection logic based on data characteristics
and question context. This serves as the single source of truth for chart type rules.
"""

# Keywords that indicate time-series data
TIME_KEYWORDS = [
    "month",
    "date",
    "year",
    "time",
    "day",
    "week",
    "quarter",
    "ym",
    "ymd",
]

# Question keywords that suggest line charts
LINE_CHART_KEYWORDS = ["trend", "over time", "timeline", "progression"]

# Question keywords that suggest scatter plots
SCATTER_CHART_KEYWORDS = ["correlation", "relationship", "scatter", "compare"]

# Question keywords that suggest pie charts
PIE_CHART_KEYWORDS = ["distribution", "proportion", "percentage", "share"]

# Time patterns to exclude from pie charts
TIME_PATTERNS = [
    "q1",
    "q2",
    "q3",
    "q4",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]

# Column name keywords that suggest categorical data
CATEGORICAL_KEYWORDS = ["category", "type", "segment", "group"]

# Chart type selection thresholds
CHART_THRESHOLDS = {
    "pie_max_categories": 8,
    "pie_min_categories": 2,
    "quarter_max_points": 4,
    "scatter_min_unique_values": 10,
}
