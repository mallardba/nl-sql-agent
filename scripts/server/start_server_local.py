#!/usr/bin/env python3
"""
Production server launcher for NL-SQL Agent.
Starts the FastAPI server in production mode.
"""

import subprocess
import sys


def run_server():
    """Run uvicorn in production mode."""
    print()
    print("🚀 Starting Local NL-SQL Agent Server")
    print("=" * 50)
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    try:
        # Start uvicorn in production mode
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ]
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    run_server()
