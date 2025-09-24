#!/usr/bin/env python3
"""
Ask a question and open the result in a web browser.

This script sends a question to the NL-SQL Agent and opens the HTML response
directly in the default web browser.
"""

import sys
import urllib.parse
import webbrowser
from typing import Optional


def ask_and_open(question: Optional[str] = None) -> None:
    """
    Ask a question and open the result in a web browser.

    Args:
        question: The question to ask. If None, will prompt for input.
    """
    if not question:
        question = input("Enter your question: ").strip()
        if not question:
            print("No question provided. Exiting.")
            return

    # URL encode the question
    encoded_question = urllib.parse.quote(question)

    # Construct the URL
    url = f"http://localhost:8000/ask-html?question={encoded_question}"

    print(f"🔍 Asking: {question}")
    print(f"🌐 Opening: {url}")

    # Open in default web browser
    try:
        webbrowser.open(url)
        print("✅ Opened in browser")
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        print(f"Please manually open: {url}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Question provided as command line argument
        question = " ".join(sys.argv[1:])
        ask_and_open(question)
    else:
        # Interactive mode
        ask_and_open()


if __name__ == "__main__":
    main()
