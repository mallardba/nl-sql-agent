#!/usr/bin/env python3
"""
Run the NL-SQL Agent with debug mode enabled.
This script sets the DEBUG environment variable and starts uvicorn.
"""

import os
import subprocess
import sys


def run_debug_server():
    """Run uvicorn with debug mode enabled."""
    # Store original DEBUG value
    original_debug = os.environ.get("DEBUG", "false")

    try:
        # Set debug environment variable
        os.environ["DEBUG"] = "true"

        print("🚀 Starting NL-SQL Agent in DEBUG mode")
        print("=" * 50)
        print("Debug output will show:")
        print("  • AI generated SQL queries")
        print("  • SQL fixes applied")
        print("  • Chart column selections")
        print("  • Heuristic fallback queries")
        print("=" * 50)
        print()

        # Start uvicorn with debug mode
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--port",
                "8000",
            ]
        )
    except KeyboardInterrupt:
        print("\n🛑 Debug server stopped")
    finally:
        # Reset DEBUG environment variable to original value
        os.environ["DEBUG"] = original_debug
        print(f"🔧 DEBUG reset to: {original_debug}")


if __name__ == "__main__":
    run_debug_server()
