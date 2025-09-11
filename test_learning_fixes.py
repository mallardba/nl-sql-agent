#!/usr/bin/env python3
"""
Test script to verify learning metrics fixes and error logging.
"""

import time

import requests

BASE_URL = "http://localhost:8000"


def test_learning_metrics():
    """Test that learning metrics are properly recorded."""
    print("🧪 Testing Learning Metrics Recording")
    print("=" * 50)

    # Test questions that should generate different categories
    test_questions = [
        "What are the top 5 products by revenue?",  # revenue
        "Show me customer distribution by region",  # customer
        "What's the trend in sales over time?",  # time_series
        "Find products with low inventory",  # product
        "How many orders were placed last month?",  # reporting
        "Compare revenue between Q1 and Q2",  # analytics
    ]

    print("Sending test queries...")
    for i, question in enumerate(test_questions, 1):
        print(f"  {i}. {question}")
        try:
            response = requests.post(
                f"{BASE_URL}/ask", json={"question": question}, timeout=30
            )
            if response.status_code == 200:
                print("     ✅ Success")
            else:
                print(f"     ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"     ❌ Error: {e}")
        time.sleep(1)  # Small delay between requests

    print("\n📊 Checking Learning Metrics...")
    try:
        metrics_response = requests.get(f"{BASE_URL}/learning/metrics")
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            print(f"Total queries: {metrics.get('total_queries', 0)}")
            print(f"Successful queries: {metrics.get('successful_queries', 0)}")
            print(f"Success rate: {metrics.get('success_rate', 0):.1%}")

            print("\nCategory Performance:")
            category_perf = metrics.get("category_performance", {})
            for category, perf in category_perf.items():
                if perf.get("total", 0) > 0:
                    print(
                        f"  {category}: {perf['successful']}/{perf['total']} ({perf.get('success_rate', 0):.1%})"
                    )

            print("\nAccuracy by Source:")
            accuracy_by_source = metrics.get("accuracy_by_source", {})
            for source, count in accuracy_by_source.items():
                print(f"  {source}: {count} successful")
        else:
            print(f"❌ Failed to get metrics: {metrics_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting metrics: {e}")


def test_error_logging():
    """Test error logging functionality."""
    print("\n🔍 Testing Error Logging")
    print("=" * 50)

    # Try a question that might cause an error
    problematic_question = "Show me data from a non-existent table called 'fake_table'"

    print(f"Sending problematic query: {problematic_question}")
    try:
        response = requests.post(
            f"{BASE_URL}/ask", json={"question": problematic_question}, timeout=30
        )
        print(f"Response status: {response.status_code}")
    except Exception as e:
        print(f"Request error: {e}")

    print("\nChecking error logs...")
    try:
        error_logs_response = requests.get(f"{BASE_URL}/errors/logs?limit=10")
        if error_logs_response.status_code == 200:
            logs = error_logs_response.json()
            print(f"Found {len(logs)} error log entries")
            if logs:
                latest_log = logs[-1]
                print(f"Latest error: {latest_log.get('error_type', 'unknown')}")
                print(f"Question: {latest_log.get('question', 'N/A')}")
                print(f"Error: {latest_log.get('error_message', 'N/A')[:100]}...")
        else:
            print(f"❌ Failed to get error logs: {error_logs_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting error logs: {e}")

    print("\nChecking error summary...")
    try:
        error_summary_response = requests.get(f"{BASE_URL}/errors/summary")
        if error_summary_response.status_code == 200:
            summary = error_summary_response.json()
            print(f"Total errors: {summary.get('total_errors', 0)}")
            print(f"Error types: {summary.get('error_types', {})}")
        else:
            print(
                f"❌ Failed to get error summary: {error_summary_response.status_code}"
            )
    except Exception as e:
        print(f"❌ Error getting error summary: {e}")


def main():
    """Run all tests."""
    print("🚀 Learning Metrics & Error Logging Test")
    print("=" * 60)
    print()

    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server is not running. Please start with:")
            print(
                "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
            )
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return

    print()
    test_learning_metrics()
    test_error_logging()

    print("\n✅ Test completed!")
    print("\n🎯 Expected Results:")
    print("  - Learning metrics should show non-zero values")
    print("  - Category performance should show successful queries")
    print("  - Accuracy by source should show successful counts")
    print("  - Error logs should be created in logs/ directory")
    print("  - Error summary should show error statistics")


if __name__ == "__main__":
    main()
