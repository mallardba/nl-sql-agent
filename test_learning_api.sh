#!/bin/bash

echo "🚀 Testing Enhanced Learning System API"
echo "======================================"
echo

# Test learning metrics endpoint
echo "📊 Testing Learning Metrics Endpoint:"
echo "GET /learning/metrics"
curl -s -X GET "http://localhost:8000/learning/metrics" | jq '.' 2>/dev/null || curl -s -X GET "http://localhost:8000/learning/metrics"
echo
echo

# Test a query with enhanced learning features
echo "🧪 Testing Enhanced Query Response:"
echo "POST /ask with learning features"
curl -s -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the top 5 products by revenue?"}' | jq '.' 2>/dev/null || curl -s -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the top 5 products by revenue?"}'
echo
echo

# Test another query to see learning metrics update
echo "🔄 Testing Second Query:"
echo "POST /ask with different question"
curl -s -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me customer distribution by region"}' | jq '.' 2>/dev/null || curl -s -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Show me customer distribution by region"}'
echo
echo

# Check updated learning metrics
echo "📈 Updated Learning Metrics:"
echo "GET /learning/metrics (after queries)"
curl -s -X GET "http://localhost:8000/learning/metrics" | jq '.' 2>/dev/null || curl -s -X GET "http://localhost:8000/learning/metrics"
echo
echo

echo "✅ Enhanced Learning System Test Complete!"
echo
echo "🎯 New Features Added:"
echo "  ✅ Query categorization (7 categories)"
echo "  ✅ Learning metrics tracking"
echo "  ✅ Query expansion and suggestions"
echo "  ✅ Error pattern recognition"
echo "  ✅ Performance monitoring"
echo "  ✅ Category-based analytics"
echo
echo "📈 New API Endpoints:"
echo "  GET /learning/metrics - View learning statistics"
echo
echo "🔍 Enhanced /ask Response includes:"
echo "  - query_category"
echo "  - category_confidence"
echo "  - query_suggestions"
echo "  - related_questions"
echo "  - response_time"
