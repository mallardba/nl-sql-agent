#!/usr/bin/env python3
"""
Heuristic SQL Generation Tester

Tests the heuristic SQL generation system by sending questions that should
trigger heuristic patterns and verifying the responses.
"""

import json
import sys
import time
from typing import Any, Dict, List

import requests


def test_heuristic_generation(
    question: str,
    base_url: str = "http://localhost:8000",
    timeout: int = 30,
    force_heuristic: bool = True,
) -> Dict[str, Any]:
    """
    Test heuristic SQL generation for a specific question.

    Args:
        question: The question to test
        base_url: Base URL of the NL-SQL Agent
        timeout: Request timeout in seconds
        force_heuristic: If True, force heuristic generation (disable AI)

    Returns:
        Dictionary with test results
    """
    print(f"🔍 Testing: {question}")

    try:
        response = requests.post(
            f"{base_url}/ask",
            headers={"Content-Type": "application/json"},
            json={"question": question, "force_heuristic": force_heuristic},
            timeout=timeout,
        )

        if response.status_code == 200:
            data = response.json()

            # Check if heuristic was used
            sql_source = data.get("sql_source", "unknown")
            sql_corrected = data.get("sql_corrected", False)
            rows = data.get("rows", [])

            result = {
                "question": question,
                "success": True,
                "sql_source": sql_source,
                "sql_corrected": sql_corrected,
                "row_count": len(rows),
                "sql": data.get("sql", ""),
                "answer_text": data.get("answer_text", ""),
                "error": None,
            }

            # Determine if heuristic was used
            is_heuristic = sql_source in ["heuristic", "heuristic_fallback"]

            if is_heuristic:
                print(f"  ✅ Heuristic used ({sql_source})")
                if sql_corrected:
                    print("  🔧 SQL was corrected")
                print(f"  📊 Returned {len(rows)} rows")
            else:
                print(f"  ⚠️  Non-heuristic source: {sql_source}")

            return result

        else:
            error_result = {
                "question": question,
                "success": False,
                "sql_source": "error",
                "sql_corrected": False,
                "row_count": 0,
                "sql": "",
                "answer_text": "",
                "error": f"HTTP {response.status_code}: {response.text}",
            }
            print(f"  ❌ HTTP Error: {response.status_code}")
            return error_result

    except requests.exceptions.ConnectionError:
        error_result = {
            "question": question,
            "success": False,
            "sql_source": "error",
            "sql_corrected": False,
            "row_count": 0,
            "sql": "",
            "answer_text": "",
            "error": "Connection refused - server not running",
        }
        print("  ❌ Connection Error: Server not running")
        return error_result

    except requests.exceptions.Timeout:
        error_result = {
            "question": question,
            "success": False,
            "sql_source": "error",
            "sql_corrected": False,
            "row_count": 0,
            "sql": "",
            "answer_text": "",
            "error": f"Request timeout ({timeout}s)",
        }
        print(f"  ⏰ Timeout Error: Request took longer than {timeout}s")
        return error_result

    except Exception as e:
        error_result = {
            "question": question,
            "success": False,
            "sql_source": "error",
            "sql_corrected": False,
            "row_count": 0,
            "sql": "",
            "answer_text": "",
            "error": str(e),
        }
        print(f"  ❌ Unexpected Error: {e}")
        return error_result


def run_heuristic_tests(
    base_url: str = "http://localhost:8000", force_heuristic: bool = True
) -> List[Dict[str, Any]]:
    """
    Run a comprehensive set of heuristic generation tests.

    Args:
        base_url: Base URL of the NL-SQL Agent
        force_heuristic: If True, force heuristic generation (disable AI)

    Returns:
        List of test results
    """
    # Test questions designed to trigger heuristic patterns
    test_questions = [
        # Revenue/Sales patterns
        "top 5 products by revenue",
        "best selling products this year",
        "highest revenue customers",
        "most profitable product categories",
        # Time-based patterns
        "sales by month",
        "monthly sales trends",
        "quarterly revenue comparison",
        "revenue trends over time",
        # Customer patterns
        "top 10 customers",
        "customer order value",
        "new customers this month",
        # Product patterns
        "products with low inventory",
        "product performance by category",
        "items with highest profit margins",
        # Order patterns
        "order status distribution",
        "recent orders",
        # Simple aggregation tests
        "total revenue",
        "count of orders",
        "average order size",
    ]

    print("🚀 Starting Heuristic SQL Generation Tests")
    if force_heuristic:
        print("🔒 AI DISABLED - Forcing Heuristic Generation")
    print("=" * 50)
    print()

    results = []

    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] ", end="")
        result = test_heuristic_generation(
            question, base_url, force_heuristic=force_heuristic
        )
        results.append(result)

        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
        print()

    return results


def analyze_results(results: List[Dict[str, Any]]) -> None:
    """
    Analyze and display test results.

    Args:
        results: List of test results
    """
    print("📊 Test Results Analysis")
    print("=" * 30)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    heuristic_tests = sum(
        1 for r in results if r["sql_source"] in ["heuristic", "heuristic_fallback"]
    )
    corrected_tests = sum(1 for r in results if r["sql_corrected"])

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests} ({successful_tests/total_tests:.1%})")
    print(f"Heuristic Used: {heuristic_tests} ({heuristic_tests/total_tests:.1%})")
    print(f"SQL Corrected: {corrected_tests} ({corrected_tests/total_tests:.1%})")
    print()

    # Show source breakdown
    sources = {}
    for result in results:
        source = result["sql_source"]
        sources[source] = sources.get(source, 0) + 1

    print("SQL Source Breakdown:")
    for source, count in sources.items():
        print(f"  {source}: {count} ({count/total_tests:.1%})")
    print()

    # Show failed tests
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print("❌ Failed Tests:")
        for result in failed_tests:
            print(f"  - {result['question']}: {result['error']}")
        print()

    # Show non-heuristic tests
    non_heuristic = [
        r
        for r in results
        if r["sql_source"] not in ["heuristic", "heuristic_fallback"] and r["success"]
    ]
    if non_heuristic:
        print("⚠️  Tests that didn't use heuristic:")
        for result in non_heuristic:
            print(f"  - {result['question']}: {result['sql_source']}")
        print()


def main():
    """Main entry point."""
    base_url = "http://localhost:8000"
    force_heuristic = True  # Default to forcing heuristics

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Heuristic SQL Generation Tester")
            print("=" * 35)
            print()
            print("Usage: python run_heuristic_generation.py [options] [question]")
            print()
            print("Options:")
            print(
                "  --allow-ai          Allow AI generation (default: force heuristic)"
            )
            print("  -h, --help          Show this help message")
            print()
            print("Arguments:")
            print("  question            Test a specific question")
            print()
            print("By default, this script forces heuristic generation to test")
            print("the heuristic system exclusively. Use --allow-ai to enable AI.")
            return
        elif sys.argv[1] == "--allow-ai":
            force_heuristic = False
            if len(sys.argv) > 2:
                # Test single question with AI allowed
                question = " ".join(sys.argv[2:])
                print("🔍 Single Question Test (AI Allowed)")
                print("=" * 40)
                print()

                result = test_heuristic_generation(
                    question, base_url, force_heuristic=False
                )

                print()
                print("📊 Result:")
                print(f"Question: {result['question']}")
                print(f"Success: {result['success']}")
                print(f"SQL Source: {result['sql_source']}")
                print(f"SQL Corrected: {result['sql_corrected']}")
                print(f"Rows Returned: {result['row_count']}")
                if result["error"]:
                    print(f"Error: {result['error']}")
                return
        else:
            # Test single question
            question = " ".join(sys.argv[1:])
            print("🔍 Single Question Heuristic Test (Forced)")
            print("=" * 45)
            print()

            result = test_heuristic_generation(question, base_url)

            print()
            print("📊 Result:")
            print(f"Question: {result['question']}")
            print(f"Success: {result['success']}")
            print(f"SQL Source: {result['sql_source']}")
            print(f"SQL Corrected: {result['sql_corrected']}")
            print(f"Rows Returned: {result['row_count']}")
            if result["error"]:
                print(f"Error: {result['error']}")
            return

    # Run comprehensive tests
    try:
        results = run_heuristic_tests(base_url, force_heuristic=force_heuristic)
        analyze_results(results)

        # Save results to file
        output_file = "test_heuristic_generation_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to: {output_file}")

    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
