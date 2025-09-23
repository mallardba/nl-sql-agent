curl -X POST "http://localhost:8000/ask?html=true" \
  -H "Content-Type: application/json" \
  -d '{"question":"top 5 products by revenue last 6 months"}'