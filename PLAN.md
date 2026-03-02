# Implementation Plan: API Testing Infrastructure

## Objective
Enhance the testing framework with API endpoint tests, pytest configuration, and improved test fixtures.

## Current State
- **Existing tests**: `test_ai_generator.py`, `test_rag_system.py`, `test_search_tools.py`, `test_vector_store.py`
- **Existing fixtures**: `conftest.py` with basic fixtures (temp paths, mock stores, sample data)
- **Missing**: API endpoint tests, pytest configuration, API-specific fixtures

## Challenge
The FastAPI app (`backend/app.py`) mounts static files from `../frontend` at root path, which causes issues in isolated test environments.

## Solution Approach
Create a **separate test app** that exposes the same API routes without static file mounting, allowing isolated endpoint testing.

---

## Implementation Steps

### Step 1: Add pytest configuration to pyproject.toml
Create `pyproject.toml` in the worktree root with pytest configuration:
- Add `[tool.pytest.ini_options]` section
- Configure test paths, markers, and output options
- Set appropriate test discovery patterns

### Step 2: Create API test fixtures in conftest.py
Add fixtures to `backend/tests/conftest.py`:
- `test_app`: FastAPI TestClient fixture with mocked RAG system
- `mock_rag_system`: Fixture to mock RAGSystem for API tests
- `mock_query_response`: Sample query response data
- `mock_course_stats`: Sample course statistics data

### Step 3: Create API endpoint tests
Create `backend/tests/test_api.py` with tests for:
- `POST /api/query` endpoint
  - Test successful query with response
  - Test query without session_id (auto-creation)
  - Test query with existing session_id
  - Test error handling (500 errors)
- `GET /api/courses` endpoint
  - Test successful retrieval of course stats
  - Test error handling
- `POST /api/new-chat` endpoint
  - Test session creation
  - Test error handling

### Step 4: Create test-specific FastAPI router
To avoid static file mounting issues, extract API routes into a router that can be:
- Included in the main app (for production)
- Mounted in a test app (for testing)

This approach:
- Avoids importing the full app with static mounts
- Allows proper mocking of RAG system
- Provides clean separation for testing

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Create | pytest configuration |
| `backend/tests/conftest.py` | Modify | Add API test fixtures |
| `backend/tests/test_api.py` | Create | API endpoint tests |
| `backend/app.py` | Modify | Extract routes to router (optional, for cleaner testing) |

---

## Detailed Implementation

### 1. pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### 2. conftest.py additions
- `test_client`: FastAPI TestClient with mocked dependencies
- `mock_rag_system`: MagicMock configured for API testing
- Sample response fixtures for assertions

### 3. test_api.py structure
- `TestQueryEndpoint`: Tests for POST /api/query
- `TestCoursesEndpoint`: Tests for GET /api/courses
- `TestNewChatEndpoint`: Tests for POST /api/new-chat
- `TestAPIErrorHandling`: Error scenario tests

---

## Testing the Implementation
After implementation, run:
```bash
uv run pytest backend/tests/test_api.py -v
uv run pytest backend/tests/ -v  # Run all tests
```