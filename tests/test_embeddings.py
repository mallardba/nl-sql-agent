#!/usr/bin/env python3
"""
Test script for ChromaDB embeddings setup.
Run this to verify that embeddings are working.
"""

import pytest
import requests


def test_embeddings_setup():
    """Test the embeddings system."""
    base_url = "http://localhost:8000"

    print("🧪 Testing Embeddings Setup")
    print("=" * 40)

    # Skip this test in CI/pre-commit environments to avoid file modifications
    import os

    if os.getenv("CI") or os.getenv("PRE_COMMIT"):
        pytest.skip("Skipping integration test in CI/pre-commit environment")

    # Test 1: Check embeddings status
    print("1. Checking embeddings status...")
    try:
        response = requests.get(f"{base_url}/embeddings/status", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"📊 Embeddings: {data['embeddings']}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Server not available: {e}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        raise

    # Test 2: Initialize schema embeddings
    print("\n2. Initializing schema embeddings...")
    try:
        response = requests.post(f"{base_url}/embeddings/initialize", timeout=5)
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code} - {response.text}"
        data = response.json()
        print(f"✅ {data['message']}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Server not available: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    # Test 3: Check status again
    print("\n3. Checking status after initialization...")
    try:
        response = requests.get(f"{base_url}/embeddings/status", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"✅ Final status: {data['status']}")
        print(f"📊 Final embeddings: {data['embeddings']}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Server not available: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    print("\n🎉 Embeddings setup test completed successfully!")


if __name__ == "__main__":
    print(
        "Make sure your FastAPI server is running: python -m uvicorn app.main:app --reload"
    )
    print("Then run this test script.\n")

    try:
        test_embeddings_setup()
        print("\n✅ Embeddings system is working correctly!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
