#!/bin/bash
question="$1"
curl -X POST "http://localhost:8000/ask?html=true" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$question\"}" \
  -o response.html
start response.html
