"""
Enhanced Learning System for NL-SQL Agent.
Implements query categorization, pattern recognition, and learning metrics.
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple

from .cache import get_cache, set_cache


class QueryCategorizer:
    """Categorizes queries into different types for better pattern recognition."""

    def __init__(self):
        self.categories = {
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

    def categorize_query(self, question: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Categorize a query and return category, confidence, and metadata.

        Returns:
            Tuple of (category, confidence_score, metadata)
        """
        if not question or not isinstance(question, str):
            return "unknown", 0.0, {}

        question_lower = question.lower()
        scores = {}
        metadata = {}

        for category, config in self.categories.items():
            score = 0.0
            matched_keywords = []
            matched_patterns = []

            # Score based on keywords
            for keyword in config["keywords"]:
                if keyword in question_lower:
                    score += 1.0
                    matched_keywords.append(keyword)

            # Score based on patterns (higher weight)
            for pattern in config["patterns"]:
                if pattern in question_lower:
                    score += 2.0
                    matched_patterns.append(pattern)

            # Normalize score by question length
            normalized_score = score / max(len(question.split()), 1)
            scores[category] = normalized_score

            metadata[category] = {
                "matched_keywords": matched_keywords,
                "matched_patterns": matched_patterns,
                "raw_score": score,
                "normalized_score": normalized_score,
            }

        # Find best category
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        return best_category, confidence, metadata


class LearningMetrics:
    """Tracks learning metrics and improvement over time."""

    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "ai_generated": 0,
            "heuristic_fallback": 0,
            "sql_corrected": 0,
            "cache_hits": 0,
            "error_patterns": defaultdict(int),
            "category_performance": defaultdict(lambda: {"total": 0, "successful": 0}),
            "query_complexity": defaultdict(int),
            "response_times": [],
            "accuracy_by_source": {"ai": 0, "heuristic": 0, "cache": 0},
        }

    def record_query(self, question: str, result: Dict[str, Any], response_time: float):
        """Record a query and its result for learning metrics."""
        self.metrics["total_queries"] += 1
        self.metrics["response_times"].append(response_time)

        # Track success - check if we have rows and no error details
        has_rows = result.get("rows") is not None and len(result.get("rows", [])) > 0
        has_error = "error_details" in result
        is_successful = has_rows and not has_error

        if is_successful:
            self.metrics["successful_queries"] += 1

        # Track source
        sql_source = result.get("sql_source", "unknown")
        if sql_source == "ai":
            self.metrics["ai_generated"] += 1
        elif sql_source == "heuristic":
            self.metrics["heuristic_fallback"] += 1
        elif sql_source == "cache":
            self.metrics["cache_hits"] += 1

        # Track source totals for accuracy calculation
        if "source_totals" not in self.metrics:
            self.metrics["source_totals"] = {"ai": 0, "heuristic": 0, "cache": 0}
        self.metrics["source_totals"][sql_source] += 1

        # Track corrections
        if result.get("sql_corrected", False):
            self.metrics["sql_corrected"] += 1

        # Track category performance
        categorizer = QueryCategorizer()
        category, confidence, _ = categorizer.categorize_query(question)
        self.metrics["category_performance"][category]["total"] += 1
        if is_successful:
            self.metrics["category_performance"][category]["successful"] += 1

        # Track query complexity (simple heuristic)
        complexity = self._calculate_complexity(question)
        self.metrics["query_complexity"][complexity] += 1

        # Update accuracy by source
        if is_successful:
            self.metrics["accuracy_by_source"][sql_source] += 1

    def record_error(self, error_type: str, error_message: str):
        """Record an error pattern for learning."""
        self.metrics["error_patterns"][error_type] += 1

    def _calculate_complexity(self, question: str) -> str:
        """Calculate query complexity based on question characteristics."""
        q = question.lower()

        # Simple complexity heuristics
        if any(word in q for word in ["join", "multiple", "compare", "correlation"]):
            return "high"
        elif any(word in q for word in ["group by", "order by", "where", "having"]):
            return "medium"
        else:
            return "low"

    def get_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics."""
        metrics = dict(self.metrics)

        # Calculate derived metrics
        if metrics["total_queries"] > 0:
            metrics["success_rate"] = (
                metrics["successful_queries"] / metrics["total_queries"]
            )
            metrics["ai_usage_rate"] = (
                metrics["ai_generated"] / metrics["total_queries"]
            )
            metrics["correction_rate"] = (
                metrics["sql_corrected"] / metrics["total_queries"]
            )
            metrics["cache_hit_rate"] = metrics["cache_hits"] / metrics["total_queries"]

            if metrics["response_times"]:
                metrics["avg_response_time"] = sum(metrics["response_times"]) / len(
                    metrics["response_times"]
                )
            else:
                metrics["avg_response_time"] = 0.0
        else:
            metrics["success_rate"] = 0.0
            metrics["ai_usage_rate"] = 0.0
            metrics["correction_rate"] = 0.0
            metrics["cache_hit_rate"] = 0.0
            metrics["avg_response_time"] = 0.0

        # Calculate category success rates
        for category, perf in metrics["category_performance"].items():
            if perf["total"] > 0:
                perf["success_rate"] = perf["successful"] / perf["total"]
            else:
                perf["success_rate"] = 0.0

        # Calculate accuracy by source as fractions/percentages
        source_totals = metrics.get(
            "source_totals", {"ai": 0, "heuristic": 0, "cache": 0}
        )
        accuracy_by_source = {}
        for source, successful_count in metrics["accuracy_by_source"].items():
            total_count = source_totals.get(source, 0)
            if total_count > 0:
                accuracy_by_source[source] = {
                    "successful": successful_count,
                    "total": total_count,
                    "accuracy_rate": successful_count / total_count,
                    "accuracy_percentage": f"{(successful_count / total_count) * 100:.1f}%",
                }
            else:
                accuracy_by_source[source] = {
                    "successful": 0,
                    "total": 0,
                    "accuracy_rate": 0.0,
                    "accuracy_percentage": "0.0%",
                }

        metrics["accuracy_by_source"] = accuracy_by_source

        return metrics

    def save_metrics(self):
        """Save metrics to cache for persistence."""
        set_cache("learning_metrics", self.get_metrics(), ttl=24 * 60 * 60)  # 24 hours

    def load_metrics(self):
        """Load metrics from cache."""
        cached = get_cache("learning_metrics")
        if cached:
            self.metrics.update(cached)


class QueryExpander:
    """Provides query expansion and suggestions based on similar queries."""

    def __init__(self):
        self.suggestion_patterns = {
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

    def get_suggestions(
        self, question: str, category: str, n_suggestions: int = 3
    ) -> List[str]:
        """Get query suggestions based on the question and category."""
        suggestions = []

        # Get category-specific suggestions
        if category in self.suggestion_patterns:
            suggestions.extend(self.suggestion_patterns[category][:n_suggestions])

        # Add general suggestions if we need more
        if len(suggestions) < n_suggestions:
            general_suggestions = [
                "What are the top 5 products by revenue?",
                "Show me customer distribution by region",
                "What's our total sales this month?",
                "Which products have the highest profit margins?",
            ]
            suggestions.extend(general_suggestions[: n_suggestions - len(suggestions)])

        return suggestions[:n_suggestions]

    def get_related_questions(
        self, question: str, similar_queries: List[Dict[str, Any]]
    ) -> List[str]:
        """Get related questions based on similar queries in the database."""
        related = []

        for query_info in similar_queries[:3]:  # Top 3 similar
            if query_info.get("question") and query_info["question"] != question:
                related.append(query_info["question"])

        return related


# Global instances
_categorizer = QueryCategorizer()
_metrics = LearningMetrics()
_expander = QueryExpander()

# Load existing metrics
_metrics.load_metrics()


def categorize_query(question: str) -> Tuple[str, float, Dict[str, Any]]:
    """Categorize a query using the global categorizer."""
    return _categorizer.categorize_query(question)


def record_query_metrics(question: str, result: Dict[str, Any], response_time: float):
    """Record query metrics using the global metrics tracker."""
    _metrics.record_query(question, result, response_time)
    _metrics.save_metrics()


def record_error_metrics(error_type: str, error_message: str):
    """Record error metrics using the global metrics tracker."""
    _metrics.record_error(error_type, error_message)
    _metrics.save_metrics()


def get_learning_metrics() -> Dict[str, Any]:
    """Get current learning metrics."""
    return _metrics.get_metrics()


def get_query_suggestions(
    question: str, category: str, n_suggestions: int = 3
) -> List[str]:
    """Get query suggestions using the global expander."""
    return _expander.get_suggestions(question, category, n_suggestions)


def get_related_questions(
    question: str, similar_queries: List[Dict[str, Any]]
) -> List[str]:
    """Get related questions using the global expander."""
    return _expander.get_related_questions(question, similar_queries)
