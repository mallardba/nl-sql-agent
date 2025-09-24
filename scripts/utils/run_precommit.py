#!/usr/bin/env python3
"""
Pre-commit Runner

Runs pre-commit hooks on all files with enhanced error handling and user feedback.
"""

import subprocess
import sys
from pathlib import Path


def check_precommit_installed() -> bool:
    """
    Check if pre-commit is installed and available.

    Returns:
        True if pre-commit is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_precommit_hooks(all_files: bool = True) -> bool:
    """
    Run pre-commit hooks on files.

    Args:
        all_files: If True, run on all files. If False, run on staged files only.

    Returns:
        True if all hooks passed, False otherwise
    """
    print("🔍 Running pre-commit hooks...")
    print("=" * 40)

    # Check if pre-commit is installed
    if not check_precommit_installed():
        print("❌ pre-commit is not installed or not available in PATH")
        print("Please install it with:")
        print("  pip install pre-commit")
        print("  pre-commit install")
        return False

    # Build command
    cmd = ["pre-commit", "run"]
    if all_files:
        cmd.append("-a")
        print("📁 Running on all files...")
    else:
        print("📁 Running on staged files only...")

    print(f"🚀 Command: {' '.join(cmd)}")
    print()

    try:
        # Run pre-commit
        result = subprocess.run(cmd, cwd=Path.cwd(), timeout=300)  # 5 minute timeout

        if result.returncode == 0:
            print()
            print("✅ All pre-commit hooks passed!")
            return True
        else:
            print()
            print("❌ Some pre-commit hooks failed")
            print("Please fix the issues above and try again")
            return False

    except subprocess.TimeoutExpired:
        print()
        print("⏰ Pre-commit hooks timed out (5 minutes)")
        print("This might indicate a performance issue or very large files")
        return False

    except KeyboardInterrupt:
        print()
        print("🛑 Pre-commit hooks interrupted by user")
        return False

    except Exception as e:
        print()
        print(f"❌ Unexpected error running pre-commit: {e}")
        return False


def show_precommit_info() -> None:
    """Display information about pre-commit configuration."""
    print("📋 Pre-commit Configuration Info:")
    print("=" * 40)

    # Check if .pre-commit-config.yaml exists
    config_file = Path(".pre-commit-config.yaml")
    if config_file.exists():
        print("✅ Found .pre-commit-config.yaml")

        # Try to show installed hooks
        try:
            result = subprocess.run(
                ["pre-commit", "run", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print("✅ Pre-commit is properly configured")
            else:
                print("⚠️  Pre-commit may not be properly installed")
                print("Try running: pre-commit install")
        except Exception:
            print("⚠️  Could not verify pre-commit installation")
    else:
        print("❌ No .pre-commit-config.yaml found")
        print("Pre-commit hooks may not be configured for this project")


def main():
    """Main entry point."""
    print("🔧 Pre-commit Hook Runner")
    print("=" * 30)
    print()

    # Parse command line arguments
    all_files = True
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python run_precommit.py [--staged-only]")
            print()
            print("Options:")
            print("  --staged-only    Run hooks only on staged files")
            print("  -h, --help       Show this help message")
            print()
            print(
                "By default, runs hooks on all files (equivalent to 'pre-commit run -a')"
            )
            return
        elif sys.argv[1] == "--staged-only":
            all_files = False

    # Show configuration info
    show_precommit_info()
    print()

    # Run pre-commit hooks
    success = run_precommit_hooks(all_files)

    print()
    if success:
        print("🎉 Pre-commit checks completed successfully!")
        print("You can now commit your changes with confidence.")
    else:
        print("💡 Tips for fixing pre-commit issues:")
        print("  - Run individual hooks: pre-commit run <hook-name>")
        print("  - Skip hooks temporarily: git commit --no-verify")
        print("  - Update hook versions: pre-commit autoupdate")
        print("  - Install missing hooks: pre-commit install")
        sys.exit(1)


if __name__ == "__main__":
    main()
