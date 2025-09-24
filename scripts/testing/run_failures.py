#!/usr/bin/env python3
"""
Heuristic Failure Tester

Tests error handling when heuristic SQL generation fails or produces invalid SQL.
This helps verify the system's robustness and error recovery mechanisms.
"""

import json
import sys
import time
from typing import Any, Dict, List

import requests


def test_heuristic_failure(
    question: str,
    base_url: str = "http://localhost:8000",
    timeout: int = 30,
    force_heuristic: bool = True,
) -> Dict[str, Any]:
    """
    Test error handling for a question that might cause heuristic failures.

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

            sql_source = data.get("sql_source", "unknown")
            sql_corrected = data.get("sql_corrected", False)
            rows = data.get("rows", [])
            answer_text = data.get("answer_text", "")

            # Check for error indicators
            has_error = "error" in answer_text.lower()
            ai_fallback_error = data.get("ai_fallback_error", False)

            result = {
                "question": question,
                "success": True,
                "sql_source": sql_source,
                "sql_corrected": sql_corrected,
                "row_count": len(rows),
                "sql": data.get("sql", ""),
                "answer_text": answer_text,
                "has_error": has_error,
                "ai_fallback_error": ai_fallback_error,
                "error": None,
            }

            # Analyze the result
            if has_error or ai_fallback_error:
                print("  ⚠️  Error detected in response")
                if ai_fallback_error:
                    print("  🤖 AI fallback error occurred")
                print(f"  📊 Returned {len(rows)} rows")
            elif len(rows) == 0:
                print("  ⚠️  No data returned")
            else:
                print("  ✅ Successful response")
                print(f"  📊 Returned {len(rows)} rows")

            if sql_corrected:
                print("  🔧 SQL was corrected")

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
                "has_error": True,
                "ai_fallback_error": False,
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
            "has_error": True,
            "ai_fallback_error": False,
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
            "has_error": True,
            "ai_fallback_error": False,
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
            "has_error": True,
            "ai_fallback_error": False,
            "error": str(e),
        }
        print(f"  ❌ Unexpected Error: {e}")
        return error_result


def run_failure_tests(
    base_url: str = "http://localhost:8000", force_heuristic: bool = True
) -> List[Dict[str, Any]]:
    """
    Run tests designed to potentially cause heuristic failures.

    Args:
        base_url: Base URL of the NL-SQL Agent
        force_heuristic: If True, force heuristic generation (disable AI)

    Returns:
        List of test results
    """
    # Test questions that might cause issues
    test_questions = [
        # Ambiguous questions
        "show me data",
        "what is this",
        "give me everything",
        "random query",
        # Complex queries that might fail
        "show me all customers who bought products in categories that have more than 10 items and their total spending is greater than the average customer spending",
        "find products that were returned more than 5 times in the last year and are still being sold",
        "calculate the correlation between customer satisfaction and order frequency",
        # Malformed or unclear questions
        "asdfghjkl",
        "123456789",
        "???",
        "show me the thing with the stuff",
        # Edge cases
        "show me data from the future",
        "what happened before the database was created",
        "show me customers who don't exist",
        # Very long questions
        "show me all the products and their categories and subcategories and suppliers and inventory levels and sales data and customer reviews and ratings and prices and discounts and promotions and seasonal trends and market analysis and competitor data and financial metrics and performance indicators",
        # Questions with special characters
        "show me data with @#$%^&*()",
        "what about data with 'quotes' and \"double quotes\"",
        "data with; semicolons and, commas",
        # Empty or whitespace
        "",
        "   ",
        "\n\t",
        # Non-English (if supported)
        "mostrar todos los productos",
        "afficher toutes les données",
        # Questions that might cause SQL injection attempts
        "'; DROP TABLE customers; --",
        "SELECT * FROM users WHERE id = 1 OR 1=1",
        # Very specific technical queries
        "show me the execution plan for the query that finds customers with the highest lifetime value",
        "optimize the database indexes for the orders table",
        "show me the database schema and all foreign key relationships",
    ]

    print("🚀 Starting Heuristic Failure Tests")
    if force_heuristic:
        print("🔒 AI DISABLED - Forcing Heuristic Generation")
    print("=" * 40)
    print()

    results = []

    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] ", end="")
        result = test_heuristic_failure(
            question, base_url, force_heuristic=force_heuristic
        )
        results.append(result)

        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
        print()

    return results


def analyze_failure_results(results: List[Dict[str, Any]]) -> None:
    """
    Analyze and display failure test results.

    Args:
        results: List of test results
    """
    print("📊 Failure Test Results Analysis")
    print("=" * 40)

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    error_tests = sum(1 for r in results if r["has_error"])
    ai_fallback_errors = sum(1 for r in results if r["ai_fallback_error"])
    zero_row_tests = sum(1 for r in results if r["row_count"] == 0)

    print(f"Total Tests: {total_tests}")
    print(
        f"Successful Responses: {successful_tests} ({successful_tests/total_tests:.1%})"
    )
    print(f"Error Responses: {error_tests} ({error_tests/total_tests:.1%})")
    print(
        f"AI Fallback Errors: {ai_fallback_errors} ({ai_fallback_errors/total_tests:.1%})"
    )
    print(f"Zero Row Results: {zero_row_tests} ({zero_row_tests/total_tests:.1%})")
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

    # Show error patterns
    error_patterns = {}
    for result in results:
        if result["has_error"] and result["answer_text"]:
            # Extract error type from answer text
            answer_lower = result["answer_text"].lower()
            if "sql" in answer_lower and "error" in answer_lower:
                error_patterns["SQL Error"] = error_patterns.get("SQL Error", 0) + 1
            elif "connection" in answer_lower:
                error_patterns["Connection Error"] = (
                    error_patterns.get("Connection Error", 0) + 1
                )
            elif "timeout" in answer_lower:
                error_patterns["Timeout Error"] = (
                    error_patterns.get("Timeout Error", 0) + 1
                )
            else:
                error_patterns["Other Error"] = error_patterns.get("Other Error", 0) + 1

    if error_patterns:
        print("Error Patterns:")
        for pattern, count in error_patterns.items():
            print(f"  {pattern}: {count}")
        print()

    # Show successful error handling
    successful_error_handling = sum(
        1 for r in results if r["success"] and r["has_error"]
    )
    print(
        f"Successful Error Handling: {successful_error_handling} ({successful_error_handling/total_tests:.1%})"
    )
    print("(These are cases where the system gracefully handled errors)")
    print()


def main():
    """Main entry point."""
    base_url = "http://localhost:8000"
    force_heuristic = True  # Default to forcing heuristics

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Heuristic Failure Tester")
            print("=" * 25)
            print()
            print("Usage: python run_failures.py [options] [question]")
            print()
            print("Options:")
            print(
                "  --allow-ai          Allow AI generation (default: force heuristic)"
            )
            print("  -h, --help          Show this help message")
            print()
            print("Arguments:")
            print("  question            Test a specific question for failure handling")
            print()
            print("By default, this script forces heuristic generation to test")
            print("heuristic error handling exclusively. Use --allow-ai to enable AI.")
            return
        elif sys.argv[1] == "--allow-ai":
            force_heuristic = False
            if len(sys.argv) > 2:
                # Test single question with AI allowed
                question = " ".join(sys.argv[2:])
                print("🔍 Single Question Failure Test (AI Allowed)")
                print("=" * 45)
                print()

                result = test_heuristic_failure(
                    question, base_url, force_heuristic=False
                )

                print()
                print("📊 Result:")
                print(f"Question: {result['question']}")
                print(f"Success: {result['success']}")
                print(f"SQL Source: {result['sql_source']}")
                print(f"SQL Corrected: {result['sql_corrected']}")
                print(f"Rows Returned: {result['row_count']}")
                print(f"Has Error: {result['has_error']}")
                print(f"AI Fallback Error: {result['ai_fallback_error']}")
                if result["error"]:
                    print(f"Error: {result['error']}")
                return
        else:
            # Test single question
            question = " ".join(sys.argv[1:])
            print("🔍 Single Question Failure Test (Forced)")
            print("=" * 45)
            print()

            result = test_heuristic_failure(question, base_url)

            print()
            print("📊 Result:")
            print(f"Question: {result['question']}")
            print(f"Success: {result['success']}")
            print(f"SQL Source: {result['sql_source']}")
            print(f"SQL Corrected: {result['sql_corrected']}")
            print(f"Rows Returned: {result['row_count']}")
            print(f"Has Error: {result['has_error']}")
            print(f"AI Fallback Error: {result['ai_fallback_error']}")
            if result["error"]:
                print(f"Error: {result['error']}")
            return

    # Run comprehensive tests
    try:
        results = run_failure_tests(base_url, force_heuristic=force_heuristic)
        analyze_failure_results(results)

        # Save results to file
        output_file = "test_failure_results.json"
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
