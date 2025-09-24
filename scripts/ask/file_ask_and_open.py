#!/usr/bin/env python3
"""
Ask a question and save the HTML response to a file, then open it.

This script sends a question to the NL-SQL Agent, saves the HTML response
to a file, and opens it in the default web browser.
"""

import sys
import webbrowser
from pathlib import Path
from typing import Optional

import requests


def ask_and_open_file(
    question: Optional[str] = None, output_file: str = "response.html"
) -> None:
    """
    Ask a question and save HTML response to file, then open it.

    Args:
        question: The question to ask. If None, will prompt for input.
        output_file: The filename to save the HTML response to.
    """
    if not question:
        question = input("Enter your question: ").strip()
        if not question:
            print("No question provided. Exiting.")
            return

    print(f"🔍 Asking: {question}")

    try:
        # Send POST request to get HTML response
        response = requests.post(
            "http://localhost:8000/ask?html=true",
            headers={"Content-Type": "application/json"},
            json={"question": question},
            timeout=30,
        )

        if response.status_code == 200:
            # Save HTML content to file
            output_path = Path(output_file)
            output_path.write_text(response.text, encoding="utf-8")
            print(f"✅ Response saved to: {output_path.absolute()}")

            # Open in default web browser
            try:
                webbrowser.open(f"file://{output_path.absolute()}")
                print("✅ Opened in browser")
            except Exception as e:
                print(f"❌ Error opening browser: {e}")
                print(f"Please manually open: {output_path.absolute()}")

        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("Please ensure the NL-SQL Agent is running on http://localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Question provided as command line argument
        question = " ".join(sys.argv[1:])
        ask_and_open_file(question)
    else:
        # Interactive mode
        ask_and_open_file()


if __name__ == "__main__":
    main()
