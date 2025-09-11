#!/usr/bin/env python3
"""
Test script to run various questions against the NL-SQL Agent.
This helps identify SQL errors and test the system's robustness.
"""

import json
import time
from typing import Any, Dict

import requests

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Test questions organized by category
TEST_QUESTIONS = {
    "Revenue & Sales Analysis": [
        "Top 5 products by revenue last quarter",
        "Best selling products this year",
        "Highest revenue customers last 6 months",
        "Most profitable product categories",
        "Sales by month for the last year",
        "Revenue trends over the past 6 months",
        "Quarterly sales comparison",
        "Daily sales for last week",
    ],
    "Customer Analysis": [
        "Top 10 customers by total order value",
        "Customers who haven't ordered in 3 months",
        "New customers this month",
        "Customer distribution by region",
        "Average order value by customer segment",
    ],
    "Product & Inventory": [
        "Products with low inventory",
        "Most returned products",
        "Product performance by category",
        "Items with highest profit margins",
        "Products that need restocking",
    ],
    "Business Intelligence": [
        "Order status distribution",
        "Average processing time by region",
        "Payment method preferences",
        "Return rates by product category",
        "Employee performance metrics",
        "What percentage of total revenue comes from each product category?",
        "How is our customer base distributed by region?",
        "What's the breakdown of order statuses (completed, pending, cancelled)?",
        "Which product categories make up our total sales?",
        "How are our customers distributed by segment?",
    ],
    "Advanced Analytics": [
        "Revenue growth rate month over month",
        "Customer lifetime value analysis",
        "Seasonal sales patterns",
        "Cross-selling opportunities",
        "Market share by product category",
    ],
    "Time Period Tests": [
        "Sales last year",
        "Revenue this quarter",
        "Orders in the past 3 months",
        "Performance last 6 months",
    ],
    "Aggregation Tests": [
        "Total revenue by region",
        "Average order size by month",
        "Count of orders by status",
        "Sum of discounts applied",
    ],
    "Filtering Tests": [
        "Orders over $1000",
        "Products with discount > 10%",
        "Customers from specific regions",
        "High-value transactions",
    ],
}


def run_single_question(question: str, category: str) -> Dict[str, Any]:
    """Test a single question and return results."""
    print(f"\n🔍 Testing: {question}")
    print(f"📂 Category: {category}")

    try:
        # Test JSON response
        response = requests.post(
            f"{BASE_URL}/ask",
            headers={"Content-Type": "application/json"},
            json={"question": question},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success - {len(data.get('rows', []))} rows returned")

            # Display SQL source and correction info
            sql_source = data.get("sql_source", "unknown")
            sql_corrected = data.get("sql_corrected", False)
            source_emoji = {
                "ai": "🤖",
                "heuristic": "⚙️",
                "cache": "💾",
                "error": "❌",
                "heuristic_fallback": "⚠️",
            }.get(sql_source, "❓")
            correction_emoji = "🔧" if sql_corrected else "✅"
            print(
                f"🔍 SQL Source: {source_emoji} {sql_source.upper()} {correction_emoji} {'CORRECTED' if sql_corrected else 'ORIGINAL'}"
            )

            # Check for errors in response (including AI fallback errors)
            ai_fallback_error = data.get("ai_fallback_error", False)
            if "error" in data.get("answer_text", "").lower() or ai_fallback_error:
                status = "error" if ai_fallback_error else "warning"
                emoji = "❌" if ai_fallback_error else "⚠️"
                print(f"{emoji} {status.title()}: {data.get('answer_text', '')}")
                return {
                    "question": question,
                    "category": category,
                    "status": status,
                    "message": data.get("answer_text", ""),
                    "sql": data.get("sql", ""),
                    "rows_count": len(data.get("rows", [])),
                    "chart_info": None,
                    "sql_source": data.get("sql_source", "unknown"),
                    "sql_corrected": data.get("sql_corrected", False),
                    "ai_fallback_error": ai_fallback_error,
                    "error_details": {
                        "type": (
                            "ai_fallback" if ai_fallback_error else "response_error"
                        ),
                        "description": data.get("answer_text", ""),
                        "sql_generated": data.get("sql", ""),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                }

            # Extract chart information
            chart_info = None
            if data.get("chart_json"):
                chart_data = data["chart_json"]
                if "data" in chart_data and len(chart_data["data"]) > 0:
                    trace = chart_data["data"][0]
                    # Extract axis names from layout
                    layout = chart_data.get("layout", {})
                    xaxis_title = (
                        layout.get("xaxis", {}).get("title", {}).get("text", "unknown")
                    )
                    yaxis_title = (
                        layout.get("yaxis", {}).get("title", {}).get("text", "unknown")
                    )

                    chart_info = {
                        "has_chart": True,
                        "chart_type": trace.get("type", "unknown"),
                        "x_axis": (
                            trace.get("x", [])[:3] if trace.get("x") else []
                        ),  # First 3 x values
                        "y_axis": (
                            trace.get("y", [])[:3] if trace.get("y") else []
                        ),  # First 3 y values
                        "x_name": xaxis_title,
                        "y_name": yaxis_title,
                        "trace_name": trace.get("name", "unknown"),
                        "layout_title": layout.get("title", {}).get("text", "No title"),
                    }
                    print(
                        f"📊 Chart: {chart_info['chart_type']} - X: {chart_info['x_name']}, Y: {chart_info['y_name']}"
                    )
                else:
                    chart_info = {
                        "has_chart": True,
                        "error": "Invalid chart data structure",
                    }
            else:
                chart_info = {"has_chart": False, "reason": "No chart data"}
                print("📋 Table only (no chart)")

            return {
                "question": question,
                "category": category,
                "status": "success",
                "message": "Query executed successfully",
                "sql": data.get("sql", ""),
                "rows_count": len(data.get("rows", [])),
                "chart_info": chart_info,
                "sql_source": data.get("sql_source", "unknown"),
                "sql_corrected": data.get("sql_corrected", False),
                "ai_fallback_error": data.get("ai_fallback_error", False),
                "error_details": None,  # No errors for successful cases
            }
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                "question": question,
                "category": category,
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}",
                "sql": "",
                "rows_count": 0,
                "chart_info": None,
                "sql_source": "error",
                "sql_corrected": False,
                "ai_fallback_error": False,
                "error_details": {
                    "type": "http_error",
                    "status_code": response.status_code,
                    "response_text": response.text,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return {
            "question": question,
            "category": category,
            "status": "error",
            "message": f"Request error: {str(e)}",
            "sql": "",
            "rows_count": 0,
            "chart_info": None,
            "sql_source": "error",
            "sql_corrected": False,
            "ai_fallback_error": False,
            "error_details": {
                "type": "request_exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return {
            "question": question,
            "category": category,
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "sql": "",
            "rows_count": 0,
            "chart_info": None,
            "sql_source": "error",
            "sql_corrected": False,
            "ai_fallback_error": False,
            "error_details": {
                "type": "unexpected_exception",
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }


def run_all_tests():
    """Run all test questions and generate a report."""
    print("🚀 Starting NL-SQL Agent Test Suite")
    print("=" * 60)

    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if health_response.status_code != 200:
            print(
                "❌ Server is not running. Please start with: python -m uvicorn app.main:app --reload"
            )
            return
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError):
        print(
            "❌ Cannot connect to server. Please start with: python -m uvicorn app.main:app --reload"
        )
        return

    print("✅ Server is running")

    results = []
    total_questions = sum(len(questions) for questions in TEST_QUESTIONS.values())
    current_question = 0

    for category, questions in TEST_QUESTIONS.items():
        print(f"\n📂 Testing Category: {category}")
        print("-" * 40)

        for question in questions:
            current_question += 1
            print(f"\n[{current_question}/{total_questions}]", end=" ")

            result = run_single_question(question, category)
            results.append(result)

            # Small delay to avoid overwhelming the server
            time.sleep(0.5)

    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 60)

    success_count = sum(1 for r in results if r["status"] == "success")
    warning_count = sum(1 for r in results if r["status"] == "warning")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"✅ Successful: {success_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(results)}")

    # Show errors and warnings
    if error_count > 0:
        print(f"\n❌ ERRORS ({error_count}):")
        for result in results:
            if result["status"] == "error":
                print(f"  • {result['question']}")
                print(f"    {result['message']}")

    if warning_count > 0:
        print(f"\n⚠️  WARNINGS ({warning_count}):")
        for result in results:
            if result["status"] == "warning":
                print(f"  • {result['question']}")
                print(f"    {result['message']}")

    # Show successful queries with chart information
    print(f"\n✅ SUCCESSFUL QUERIES ({success_count}):")
    chart_count = 0
    for result in results:
        if result["status"] == "success":
            chart_info = result.get("chart_info", {})
            if chart_info and chart_info.get("has_chart"):
                chart_count += 1
                chart_type = chart_info.get("chart_type", "unknown")
                x_name = chart_info.get("x_name", "unknown")
                y_name = chart_info.get("y_name", "unknown")
                print(
                    f"  📊 {result['question']} ({result['rows_count']} rows) - {chart_type} chart, X: {x_name}, Y: {y_name}"
                )
            else:
                print(
                    f"  📋 {result['question']} ({result['rows_count']} rows) - Table only"
                )

    # SQL source analysis
    sql_sources = {}
    corrected_count = 0
    ai_fallback_count = 0
    for result in results:
        source = result.get("sql_source", "unknown")
        sql_sources[source] = sql_sources.get(source, 0) + 1
        if result.get("sql_corrected", False):
            corrected_count += 1
        if result.get("ai_fallback_error", False):
            ai_fallback_count += 1

    print("\n🔍 SQL SOURCE ANALYSIS:")
    for source, count in sql_sources.items():
        emoji = {
            "ai": "🤖",
            "heuristic": "⚙️",
            "cache": "💾",
            "error": "❌",
            "heuristic_fallback": "⚠️",
        }.get(source, "❓")
        print(f"  • {emoji} {source.upper()}: {count}")
    print(f"  • 🔧 SQL corrections: {corrected_count}")
    print(f"  • ⚠️  AI fallback errors: {ai_fallback_count}")

    # Error analysis
    error_types = {}
    error_examples = []
    for result in results:
        if result.get("error_details"):
            error_type = result["error_details"]["type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
            if len(error_examples) < 3:  # Show first 3 error examples
                error_examples.append(
                    {
                        "question": result["question"],
                        "type": error_type,
                        "message": (
                            result["message"][:100] + "..."
                            if len(result["message"]) > 100
                            else result["message"]
                        ),
                    }
                )

    if error_types:
        print("\n❌ ERROR ANALYSIS:")
        for error_type, count in error_types.items():
            print(f"  • {error_type}: {count}")

        if error_examples:
            print("\n🔍 ERROR EXAMPLES:")
            for i, example in enumerate(error_examples, 1):
                print(f"  {i}. {example['question']}")
                print(f"     Type: {example['type']}")
                print(f"     Message: {example['message']}")

    # Chart analysis summary
    print("\n📊 CHART ANALYSIS:")
    print(f"  • Charts generated: {chart_count}/{success_count}")
    print(f"  • Tables only: {success_count - chart_count}/{success_count}")

    # Show chart axis examples
    chart_examples = [
        r
        for r in results
        if r["status"] == "success" and r.get("chart_info", {}).get("has_chart")
    ]
    if chart_examples:
        print("\n📈 CHART AXES EXAMPLES:")
        for i, result in enumerate(chart_examples[:5]):  # Show first 5 examples
            chart_info = result["chart_info"]
            x_sample = chart_info.get("x_axis", [])[:2]  # First 2 x values
            y_sample = chart_info.get("y_axis", [])[:2]  # First 2 y values
            print(f"  {i+1}. {result['question']}")
            print(
                f"     X-axis: {x_sample} (type: {chart_info.get('chart_type', 'unknown')})"
            )
            print(f"     Y-axis: {y_sample}")

    # Save detailed results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n💾 Detailed results saved to: test_results.json")

    print("\n🎯 Next Steps:")
    if error_count > 0:
        print(f"  • Fix {error_count} SQL errors (Step 5: SQL Error Correction)")
    if warning_count > 0:
        print(f"  • Investigate {warning_count} warnings")
    print("  • Enhance AI prompts with schema context (Step 2)")
    print("  • Add question learning patterns (Step 3)")


if __name__ == "__main__":
    run_all_tests()
