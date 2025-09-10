#!/usr/bin/env python3
"""
Setup script for Docker embeddings integration.
Run this to set up ChromaDB in Docker environment.
"""

import os
import subprocess
import time

import requests


def check_docker_running():
    """Check if Docker is running."""
    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_docker_embeddings():
    """Set up embeddings in Docker environment."""
    print("🐳 Setting up Docker Embeddings")
    print("=" * 40)

    # Check if Docker is running
    if not check_docker_running():
        print("❌ Docker is not running. Please start Docker first.")
        return False

    # Create chroma_db directory if it doesn't exist
    if not os.path.exists("chroma_db"):
        os.makedirs("chroma_db")
        print("✅ Created chroma_db directory")

    # Stop existing containers
    print("1. Stopping existing containers...")
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        print("✅ Containers stopped")
    except subprocess.CalledProcessError:
        print("⚠️  No containers to stop")

    # Start containers with new configuration
    print("2. Starting containers with embeddings support...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("✅ Containers started")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start containers: {e}")
        return False

    # Wait for MySQL to be ready
    print("3. Waiting for MySQL to be ready...")
    time.sleep(10)  # Give MySQL time to start

    # Test the setup
    print("4. Testing embeddings setup...")
    try:
        response = requests.get("http://localhost:8000/embeddings/status", timeout=5)
        if response.status_code == 200:
            print("✅ Embeddings system is accessible")
        else:
            print(f"⚠️  Embeddings system returned status: {response.status_code}")
    except requests.exceptions.RequestException:
        print("ℹ️  FastAPI server not running yet (this is expected)")
        print("   The embeddings endpoints will be available once you start the server")

    print("\n🎉 Docker embeddings setup completed!")
    print("\nNext steps:")
    print("1. Start your FastAPI server: python -m uvicorn app.main:app --reload")
    print(
        "2. Initialize embeddings: curl -X POST http://localhost:8000/embeddings/initialize"
    )
    print("3. Test the setup: python test_embeddings.py")
    print(
        "\nNote: The 404 error above is normal - the server needs to be running first."
    )

    return True


if __name__ == "__main__":
    success = setup_docker_embeddings()
    if not success:
        print("\n❌ Setup failed. Check the errors above.")
