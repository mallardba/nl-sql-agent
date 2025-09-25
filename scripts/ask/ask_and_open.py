#!/usr/bin/env python3
"""
Ask a question and open the result in a web browser.

This script sends a question to the NL-SQL Agent and opens the HTML response
directly in the default web browser.
"""

import argparse
import urllib.parse
import webbrowser
from typing import Optional


def ask_and_open(question: Optional[str] = None, force_heuristic: bool = False) -> None:
    """
    Ask a question and open the result in a web browser.

    Args:
        question: The question to ask. If None, will prompt for input.
        force_heuristic: Whether to force heuristic SQL generation instead of AI.
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
    if force_heuristic:
        url += "&force_heuristic=true"

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
    parser = argparse.ArgumentParser(
        description="Ask a question to the NL-SQL Agent and open the result in a web browser."
    )
    parser.add_argument(
        "-f",
        "--force-heuristic",
        action="store_true",
        help="Force heuristic SQL generation instead of AI.",
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="The question to ask the NL-SQL Agent.",
    )

    args = parser.parse_args()

    if args.question:
        # Question provided as command line argument
        question = " ".join(args.question)
        ask_and_open(question, force_heuristic=args.force_heuristic)
    else:
        # Interactive mode
        ask_and_open(force_heuristic=args.force_heuristic)


if __name__ == "__main__":
    main()
