#!/usr/bin/env python3
"""
Test script to verify accuracy by source fixes.
"""


import requests

BASE_URL = "http://localhost:8000"


def test_accuracy_fixes():
    """Test that accuracy by source shows proper fractions."""
    print("🧪 Testing Accuracy by Source Fixes")
    print("=" * 50)

    # Check current metrics
    print("📊 Current Learning Metrics:")
    try:
        response = requests.get(f"{BASE_URL}/learning/metrics")
        if response.status_code == 200:
            metrics = response.json()

            print(f"Total queries: {metrics.get('total_queries', 0)}")
            print(f"AI generated: {metrics.get('ai_generated', 0)}")
            print(f"Heuristic fallback: {metrics.get('heuristic_fallback', 0)}")
            print(f"Cache hits: {metrics.get('cache_hits', 0)}")

            print("\n🎯 Accuracy by Source (New Format):")
            accuracy_by_source = metrics.get("accuracy_by_source", {})
            for source, data in accuracy_by_source.items():
                if isinstance(data, dict):
                    print(f"  {source.title()}:")
                    print(f"    Successful: {data.get('successful', 0)}")
                    print(f"    Total: {data.get('total', 0)}")
                    print(f"    Accuracy: {data.get('accuracy_percentage', '0.0%')}")
                    print(f"    Rate: {data.get('accuracy_rate', 0):.3f}")
                else:
                    print(f"  {source.title()}: {data} (old format)")

            print("\n📈 Source Totals:")
            source_totals = metrics.get("source_totals", {})
            for source, total in source_totals.items():
                print(f"  {source}: {total}")

        else:
            print(f"❌ Failed to get metrics: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_dashboard_display():
    """Test that dashboard displays accuracy correctly."""
    print("\n🎨 Testing Dashboard Display")
    print("=" * 50)

    print("Dashboard URL: http://localhost:8000/learning/dashboard")
    print("Check that accuracy by source shows:")
    print("  - X/Y queries format")
    print("  - Z.Z% accuracy format")
    print("  - Proper fractions for each source")


def main():
    """Run all tests."""
    print("🚀 Accuracy by Source Fix Test")
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

    test_accuracy_fixes()
    test_dashboard_display()

    print("\n✅ Test completed!")
    print("\n🎯 Expected Results:")
    print("  - Accuracy by source should show X/Y queries")
    print("  - Accuracy should show percentage (e.g., 95.3%)")
    print("  - Heuristic fallback should be properly tracked")
    print("  - Source totals should match individual counts")


if __name__ == "__main__":
    main()
