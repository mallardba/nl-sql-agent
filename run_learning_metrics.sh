#!/bin/bash

echo "🚀 NL-SQL Agent Learning Metrics"
echo "================================"
echo

# Check if server is running
echo "🔍 Checking if server is running..."
if curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "✅ Server is running on port 8000"
else
    echo "❌ Server is not running on port 8000"
    echo "Please start the server first with:"
    echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo
    read -p "Press Enter to continue anyway (server might start later)..."
fi

echo
echo "📊 Available Learning Metrics:"
echo "  🎨 Dashboard: http://localhost:8000/learning/dashboard"
echo "  📈 Raw JSON: http://localhost:8000/learning/metrics"
echo

# Function to open URL based on OS
open_url() {
    local url="$1"
    
    if command -v xdg-open > /dev/null; then
        # Linux
        xdg-open "$url"
    elif command -v open > /dev/null; then
        # macOS
        open "$url"
    elif command -v start > /dev/null; then
        # Windows
        start "$url"
    else
        echo "❌ Could not detect browser command"
        echo "Please open manually: $url"
        return 1
    fi
}

# Ask user which view they want
echo "🎯 Choose your view:"
echo "  1) Beautiful Dashboard (recommended)"
echo "  2) Raw JSON Metrics"
echo "  3) Both (open dashboard, show JSON in terminal)"
echo

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🎨 Opening Learning Dashboard..."
        open_url "http://localhost:8000/learning/dashboard"
        echo "✅ Dashboard opened in browser!"
        ;;
    2)
        echo "📈 Opening Raw Metrics..."
        open_url "http://localhost:8000/learning/metrics"
        echo "✅ Raw metrics opened in browser!"
        ;;
    3)
        echo "🎨 Opening Learning Dashboard..."
        open_url "http://localhost:8000/learning/dashboard"
        echo "✅ Dashboard opened in browser!"
        echo
        echo "📈 Raw Metrics (also displayed below):"
        echo "======================================"
        curl -s "http://localhost:8000/learning/metrics" | jq '.' 2>/dev/null || curl -s "http://localhost:8000/learning/metrics"
        ;;
    *)
        echo "❌ Invalid choice. Opening dashboard by default..."
        open_url "http://localhost:8000/learning/dashboard"
        ;;
esac

echo
echo "🎯 Dashboard Features:"
echo "  📊 Real-time metrics visualization"
echo "  📈 Query category performance"
echo "  ⚠️ Error pattern analysis"
echo "  🔍 Query complexity breakdown"
echo "  🎯 Accuracy by source (AI/Heuristic/Cache)"
echo "  🔄 Auto-refresh every 30 seconds"
echo
echo "💡 Pro Tips:"
echo "  - Run some queries to populate the metrics"
echo "  - Use the refresh button for manual updates"
echo "  - Dashboard updates automatically every 30 seconds"
echo "  - Check the raw JSON for detailed data structure"
echo
echo "🚀 Happy analyzing!"
