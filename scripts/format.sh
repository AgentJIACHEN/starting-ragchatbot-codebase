#!/bin/bash
# Quick format script - formats all Python files
# Usage: ./scripts/format.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Formatting code with ruff..."
uv run ruff format backend/
echo "Done!"