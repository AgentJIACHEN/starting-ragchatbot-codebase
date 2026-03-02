#!/bin/bash
# Code quality script - runs formatting, linting, and tests
# Usage: ./scripts/quality.sh [--fix] [--format] [--lint] [--test]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
FIX_MODE=false
RUN_FORMAT=true
RUN_LINT=true
RUN_TEST=false

for arg in "$@"; do
    case $arg in
        --fix)
            FIX_MODE=true
            ;;
        --format-only)
            RUN_LINT=false
            RUN_TEST=false
            ;;
        --lint-only)
            RUN_FORMAT=false
            RUN_TEST=false
            ;;
        --test)
            RUN_TEST=true
            ;;
        --all)
            RUN_TEST=true
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: $0 [--fix] [--format-only] [--lint-only] [--test] [--all]"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}=== Code Quality Checks ===${NC}"
echo ""

# Format code
if [ "$RUN_FORMAT" = true ]; then
    echo -e "${YELLOW}Running ruff format...${NC}"
    if [ "$FIX_MODE" = true ]; then
        uv run ruff format backend/
    else
        uv run ruff format --check backend/
    fi
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Formatting check passed${NC}"
    else
        if [ "$FIX_MODE" = false ]; then
            echo -e "${YELLOW}Run with --fix to auto-format${NC}"
        fi
    fi
    echo ""
fi

# Lint code
if [ "$RUN_LINT" = true ]; then
    echo -e "${YELLOW}Running ruff lint...${NC}"
    if [ "$FIX_MODE" = true ]; then
        uv run ruff check backend/ --fix
    else
        uv run ruff check backend/
    fi
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Lint check passed${NC}"
    else
        if [ "$FIX_MODE" = false ]; then
            echo -e "${YELLOW}Run with --fix to auto-fix issues${NC}"
        fi
    fi
    echo ""
fi

# Run tests
if [ "$RUN_TEST" = true ]; then
    echo -e "${YELLOW}Running pytest...${NC}"
    uv run pytest backend/tests/ -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    fi
    echo ""
fi

echo -e "${GREEN}=== Quality checks complete ===${NC}"