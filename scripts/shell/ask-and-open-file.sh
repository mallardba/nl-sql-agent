#!/bin/bash
question="$1"
curl -X POST "http://localhost:8000/ask?html=true" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$question\"}" \
  -o data/outputs/response.html
start data/outputs/response.html
