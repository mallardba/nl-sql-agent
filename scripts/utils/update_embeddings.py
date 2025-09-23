#!/usr/bin/env python3
"""
Manual ChromaDB Embeddings Update Script

This script manually triggers the regeneration of ChromaDB embeddings
by calling the FastAPI initialization endpoint.
"""

import sys

import requests


def update_embeddings():
    """Update ChromaDB embeddings via API call."""
    try:
        print("🔄 Updating ChromaDB embeddings...")

        # Make POST request to initialize embeddings
        response = requests.post("http://localhost:8000/embeddings/initialize")

        if response.status_code == 200:
            print("✅ Embeddings updated successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to update embeddings: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to FastAPI server at localhost:8000")
        print("Make sure the server is running with: docker compose up -d")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Check status
    try:
        print("\n📊 Checking embeddings status...")
        status_response = requests.get("http://localhost:8000/embeddings/status")
        if status_response.status_code == 200:
            stats = status_response.json()
            print(f"Schema embeddings: {stats['embeddings']['schema_embeddings']}")
            print(f"Question embeddings: {stats['embeddings']['question_embeddings']}")
        else:
            print(f"⚠️ Could not check status: {status_response.status_code}")
    except Exception as e:
        print(f"⚠️ Could not check status: {e}")

    return True


if __name__ == "__main__":
    success = update_embeddings()
    sys.exit(0 if success else 1)
