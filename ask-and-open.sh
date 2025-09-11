#!/bin/bash
question="$1"
# URL encode the question
encoded_question=$(echo "$question" | sed 's/ /%20/g' | sed 's/?/%3F/g' | sed 's/&/%26/g')
# Open the web interface directly
start "http://localhost:8000/ask-html?question=$encoded_question"