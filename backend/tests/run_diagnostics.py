"""
Run all diagnostic tests for the RAG chatbot.

This script runs all tests and provides a summary of which components
are working and which need fixes.
"""

import os
import subprocess
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Run all tests and display results."""
    print("=" * 60)
    print("RAG CHATBOT DIAGNOSTIC TESTS")
    print("=" * 60)
    print()

    # Get the tests directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))

    # Run pytest with verbose output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", tests_dir, "-v", "-s", "--tb=short"],
        cwd=os.path.dirname(tests_dir),
        capture_output=False,
    )

    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
