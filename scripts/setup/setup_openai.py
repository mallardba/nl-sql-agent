#!/usr/bin/env python3
"""
Setup script for OpenAI integration.
Run this to configure your API key and test the setup.
"""

import importlib.util
import os

from dotenv import load_dotenv


def setup_openai():
    """Guide user through OpenAI setup."""
    print("🚀 OpenAI Integration Setup")
    print("=" * 40)

    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ .env file found")
        load_dotenv()
    else:
        print("❌ .env file not found")
        print("Creating .env file...")

        # Create .env file
        with open(".env", "w") as f:
            f.write("# OpenAI API Configuration\n")
            f.write("OPENAI_API_KEY=your-openai-api-key-here\n")
            f.write("OPENAI_MODEL=gpt-3.5-turbo\n")
            f.write("OPENAI_TEMPERATURE=0.1\n")
            f.write("\n# Database Configuration\n")
            f.write("DATABASE_URL=mysql+pymysql://root:root@localhost:3306/sales\n")

        print("✅ .env file created")
        load_dotenv()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("\n❌ OpenAI API key not configured")
        print("\nTo get your API key:")
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Sign in or create an account")
        print("3. Click 'Create new secret key'")
        print("4. Copy the key")
        print(
            "5. Edit your .env file and replace 'your-openai-api-key-here' with your actual key"
        )
        print("\nExample .env content:")
        print("OPENAI_API_KEY=sk-1234567890abcdef...")

        return False
    else:
        print("✅ OpenAI API key configured")
        return True


def test_imports():
    """Test if LangChain packages are available."""
    print("\n🔍 Testing LangChain imports...")

    packages = ["langchain_openai", "langchain.prompts", "langchain.schema"]

    for package in packages:
        if importlib.util.find_spec(package) is None:
            print(f"❌ {package} not available")
            print("\nTo install required packages:")
            print("python -m pip install langchain langchain-openai python-dotenv")
            return False

    print("✅ LangChain packages imported successfully")
    return True


def main():
    """Main setup function."""
    print("Setting up OpenAI integration for your NL-SQL Agent...\n")

    # Test imports
    imports_ok = test_imports()

    # Setup OpenAI
    openai_ok = setup_openai()

    print("\n" + "=" * 40)
    if imports_ok and openai_ok:
        print("🎉 Setup complete! Your agent is ready to use OpenAI.")
        print("\nNext steps:")
        print("1. Start your FastAPI server: python -m uvicorn app.main:app --reload")
        print("2. Start your Docker container: docker compose up -d db")
        print("3. Test with: ./scripts/ask/ask-and-open.sh 'your question here'")
    else:
        print("⚠️  Setup incomplete. Please resolve the issues above.")
        print("\nAfter fixing issues, run this script again to verify setup.")


if __name__ == "__main__":
    main()
