"""
Summary of Diagnostic Test Results
===================================

Tests Run: 61 total
Tests Passed: 59
Tests Failed: 2

## ROOT CAUSE IDENTIFIED

The 'query failed' error is caused by an **INVALID MODEL NAME** in config.py:

    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

This model does not exist. The error from Anthropic API:
    "model `claude-sonnet-4-20250514` is not supported."

## CORRECT MODEL NAMES (as of 2026-02-28)

Available models:
- claude-opus-4-6 (most capable)
- claude-sonnet-4-6 (recommended balance)
- claude-haiku-4-5-20251001 (fastest)

## FIX REQUIRED

In backend/config.py, change line 13 from:
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
To:
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

## ADDITIONAL ISSUES FOUND

### Issue 2: Course name resolution always returns closest match

The `_resolve_course_name` method in vector_store.py uses semantic search
which ALWAYS returns the closest match, even for completely unrelated queries.

Example: Searching for "Nonexistent Course XYZ" still returns "Introduction to Python"
because it's the closest semantic match in the database.

This is a design issue that should be addressed by:
1. Adding a distance threshold to reject poor matches
2. Or requiring exact matches for course_name filter

### Test Results Summary

### Component Status:
- [PASS] CourseSearchTool.execute() - works correctly
- [PASS] ToolManager - works correctly
- [PASS] AIGenerator tool calling logic - works correctly
- [PASS] RAGSystem orchestration - works correctly
- [PASS] VectorStore search - works correctly
- [FAIL] API connection - invalid model name
- [WARN] Course name resolution - no threshold check

### Data Status:
- 4 courses loaded in database
- 528 content chunks available
- Course catalog populated
- ChromaDB functioning correctly
"""