from typing import Any, List

from .config import (
    CATEGORICAL_KEYWORDS,
    CHART_THRESHOLDS,
    LINE_CHART_KEYWORDS,
    PIE_CHART_KEYWORDS,
    SCATTER_CHART_KEYWORDS,
    TIME_KEYWORDS,
    TIME_PATTERNS,
)


def determine_chart_type(
    x_data: List[Any], y_data: List[Any], x_name: str, y_name: str, question: str
) -> str:
    """
    Determine the most appropriate chart type based on data characteristics and question context.

    Args:
        x_data: X-axis data values
        y_data: Y-axis data values
        x_name: Name of X-axis column
        y_name: Name of Y-axis column
        question: Original user question for context

    Returns:
        Chart type: 'line', 'bar', 'pie', 'scatter', or 'area'
    """

    # Convert to lowercase for analysis
    x_name_lower = x_name.lower()
    question_lower = question.lower()

    # Calculate unique values for analysis
    unique_x_values = len(set(str(x) for x in x_data))
    unique_y_values = len(set(str(y) for y in y_data))

    # 1. Time series analysis
    if any(keyword in x_name_lower for keyword in TIME_KEYWORDS):
        # For quarterly data with few points, prefer bar chart
        if (
            "quarter" in x_name_lower
            and unique_x_values <= CHART_THRESHOLDS["quarter_max_points"]
        ):
            return "bar"
        # For other time data, use line chart
        return "line"

    # 2. Question context analysis
    if any(keyword in question_lower for keyword in LINE_CHART_KEYWORDS):
        return "line"

    if any(keyword in question_lower for keyword in SCATTER_CHART_KEYWORDS):
        return "scatter"

    if any(keyword in question_lower for keyword in PIE_CHART_KEYWORDS):
        return "pie"

    # 3. Data distribution analysis

    # Pie chart for categorical data with few categories
    # But exclude time-based data (quarters, months, etc.)
    if (
        CHART_THRESHOLDS["pie_min_categories"]
        <= unique_x_values
        <= CHART_THRESHOLDS["pie_max_categories"]
    ):
        # Check if Y values are numeric (for pie chart)
        try:
            numeric_y = [float(y) for y in y_data if y is not None]
            if len(numeric_y) == len(y_data):  # All Y values are numeric
                # Check if X data contains time patterns
                x_data_lower = [str(x).lower() for x in x_data]
                has_time_pattern = any(
                    pattern in " ".join(x_data_lower) for pattern in TIME_PATTERNS
                )

                if not has_time_pattern:
                    return "pie"
        except (ValueError, TypeError):
            pass

    # Scatter plot for correlation analysis
    if (
        unique_x_values > CHART_THRESHOLDS["scatter_min_unique_values"]
        and unique_y_values > CHART_THRESHOLDS["scatter_min_unique_values"]
    ):
        try:
            # Check if both X and Y are numeric
            numeric_x = [float(x) for x in x_data if x is not None]
            numeric_y = [float(y) for y in y_data if y is not None]
            if len(numeric_x) == len(x_data) and len(numeric_y) == len(y_data):
                return "scatter"
        except (ValueError, TypeError):
            pass

    # 4. Column name analysis
    if any(keyword in x_name_lower for keyword in CATEGORICAL_KEYWORDS):
        if unique_x_values <= 6:
            return "pie"
        else:
            return "bar"

    # 5. Default to bar chart
    return "bar"
