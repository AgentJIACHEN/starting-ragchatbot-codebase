#!/bin/bash
# Quick lint script - checks code quality without modifying files
# Usage: ./scripts/lint.sh [--fix]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

FIX_MODE=false
if [ "$1" = "--fix" ]; then
    FIX_MODE=true
fi

echo "Running ruff lint..."
if [ "$FIX_MODE" = true ]; then
    uv run ruff check backend/ --fix
else
    uv run ruff check backend/
fi
echo "Done!"