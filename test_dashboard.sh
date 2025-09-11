#!/bin/bash

echo "🚀 Testing Learning Dashboard"
echo "=============================="
echo

echo "📊 Learning Dashboard URL:"
echo "http://localhost:8000/learning/dashboard"
echo

echo "📈 Raw Metrics URL:"
echo "http://localhost:8000/learning/metrics"
echo

echo "🧪 Testing Dashboard Endpoint:"
curl -s -X GET "http://localhost:8000/learning/dashboard" | head -20
echo
echo

echo "📋 Testing Raw Metrics Endpoint:"
curl -s -X GET "http://localhost:8000/learning/metrics" | jq '.' 2>/dev/null || curl -s -X GET "http://localhost:8000/learning/metrics"
echo
echo

echo "✅ Dashboard Features:"
echo "  🎨 Beautiful HTML dashboard with modern design"
echo "  📊 Key metrics cards (Total Queries, Success Rate, etc.)"
echo "  📈 Category performance breakdown"
echo "  ⚠️ Error pattern analysis"
echo "  🔍 Query complexity distribution"
echo "  🎯 Accuracy by source (AI, Heuristic, Cache)"
echo "  🔄 Auto-refresh every 30 seconds"
echo "  📱 Responsive design for mobile/desktop"
echo
echo "🎯 Usage:"
echo "  1. Open http://localhost:8000/learning/dashboard in your browser"
echo "  2. Run some queries to populate the metrics"
echo "  3. Watch the dashboard update in real-time"
echo "  4. Use the refresh button for manual updates"
