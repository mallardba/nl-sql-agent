#!/usr/bin/env python3
"""
Learning Metrics Viewer

Interactive script to view NL-SQL Agent learning metrics.
Provides options to view the dashboard, raw JSON metrics, or both.
"""

import json
import webbrowser
from typing import Optional

import requests


def check_server_health(base_url: str = "http://localhost:8000") -> bool:
    """
    Check if the NL-SQL Agent server is running.

    Args:
        base_url: Base URL of the server

    Returns:
        True if server is healthy, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def open_url(url: str) -> bool:
    """
    Open a URL in the default web browser.

    Args:
        url: URL to open

    Returns:
        True if successful, False otherwise
    """
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def get_raw_metrics(base_url: str = "http://localhost:8000") -> Optional[dict]:
    """
    Fetch raw learning metrics from the server.

    Args:
        base_url: Base URL of the server

    Returns:
        Metrics data as dict, or None if failed
    """
    try:
        response = requests.get(f"{base_url}/learning/metrics", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error fetching metrics: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching metrics: {e}")
        return None


def display_metrics_summary(metrics: dict) -> None:
    """
    Display a summary of the learning metrics.

    Args:
        metrics: Metrics data dictionary
    """
    print("\n📊 Metrics Summary:")
    print("=" * 50)

    total_queries = metrics.get("total_queries", 0)
    success_rate = metrics.get("success_rate", 0)
    avg_response_time = metrics.get("avg_response_time", 0)

    print(f"📈 Total Queries: {total_queries}")
    print(f"✅ Success Rate: {success_rate:.1%}")
    print(f"⏱️  Avg Response Time: {avg_response_time:.2f}s")

    # Show category performance
    category_performance = metrics.get("category_performance", {})
    if category_performance:
        print("\n📂 Query Categories:")
        for category, perf in category_performance.items():
            if perf.get("total", 0) > 0:
                success_rate = perf.get("success_rate", 0)
                print(
                    f"  {category}: {perf.get('successful', 0)}/{perf.get('total', 0)} ({success_rate:.1%})"
                )

    # Show error patterns
    error_patterns = metrics.get("error_patterns", {})
    if error_patterns:
        print("\n⚠️  Error Patterns:")
        for error_type, count in error_patterns.items():
            print(f"  {error_type}: {count} occurrences")


def main():
    """Main entry point."""
    print("🚀 NL-SQL Agent Learning Metrics")
    print("=" * 40)
    print()

    base_url = "http://localhost:8000"

    # Check if server is running
    print("🔍 Checking if server is running...")
    if check_server_health(base_url):
        print("✅ Server is running on port 8000")
    else:
        print("❌ Server is not running on port 8000")
        print("Please start the server first with:")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print()

        try:
            input("Press Enter to continue anyway (server might start later)...")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return

    print()
    print("📊 Available Learning Metrics:")
    print("  🎨 Dashboard: http://localhost:8000/learning/dashboard")
    print("  📈 Raw JSON: http://localhost:8000/learning/metrics")
    print()

    # Ask user which view they want
    print("🎯 Choose your view:")
    print("  1) Beautiful Dashboard (recommended)")
    print("  2) Raw JSON Metrics")
    print("  3) Both (open dashboard, show JSON in terminal)")
    print("  4) Metrics Summary (terminal only)")
    print()

    try:
        choice = input("Enter choice (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return

    dashboard_url = f"{base_url}/learning/dashboard"
    metrics_url = f"{base_url}/learning/metrics"

    if choice == "1":
        print("🎨 Opening Learning Dashboard...")
        if open_url(dashboard_url):
            print("✅ Dashboard opened in browser!")
        else:
            print("❌ Could not open browser. Please open manually:")
            print(f"   {dashboard_url}")

    elif choice == "2":
        print("📈 Opening Raw Metrics...")
        if open_url(metrics_url):
            print("✅ Raw metrics opened in browser!")
        else:
            print("❌ Could not open browser. Please open manually:")
            print(f"   {metrics_url}")

    elif choice == "3":
        print("🎨 Opening Learning Dashboard...")
        if open_url(dashboard_url):
            print("✅ Dashboard opened in browser!")
        else:
            print("❌ Could not open browser. Please open manually:")
            print(f"   {dashboard_url}")

        print()
        print("📈 Raw Metrics (also displayed below):")
        print("=" * 50)

        metrics = get_raw_metrics(base_url)
        if metrics:
            try:
                print(json.dumps(metrics, indent=2))
            except Exception as e:
                print(f"❌ Error formatting JSON: {e}")
                print(metrics)
        else:
            print("❌ Could not fetch metrics")

    elif choice == "4":
        print("📊 Fetching Metrics Summary...")
        metrics = get_raw_metrics(base_url)
        if metrics:
            display_metrics_summary(metrics)
        else:
            print("❌ Could not fetch metrics")

    else:
        print("❌ Invalid choice. Opening dashboard by default...")
        if open_url(dashboard_url):
            print("✅ Dashboard opened in browser!")
        else:
            print("❌ Could not open browser. Please open manually:")
            print(f"   {dashboard_url}")

    print()
    print("🎯 Dashboard Features:")
    print("  📊 Real-time metrics visualization")
    print("  📈 Query category performance")
    print("  ⚠️ Error pattern analysis")
    print("  🔍 Query complexity breakdown")
    print("  🎯 Accuracy by source (AI/Heuristic/Cache)")
    print("  🔄 Auto-refresh every 30 seconds")
    print()
    print("💡 Pro Tips:")
    print("  - Run some queries to populate the metrics")
    print("  - Use the refresh button for manual updates")
    print("  - Dashboard updates automatically every 30 seconds")
    print("  - Check the raw JSON for detailed data structure")
    print()
    print("🚀 Happy analyzing!")


if __name__ == "__main__":
    main()
