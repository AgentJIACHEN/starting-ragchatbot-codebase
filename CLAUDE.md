# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Dependency Management (all via uv)
```bash
# Install dependencies (including dev tools)
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Run any command in the uv environment
uv run <command>
```

### Development
```bash
# Run the development server
./run.sh           # macOS/Linux
run.bat            # Windows

# Or manually:
cd backend && uv run uvicorn app:app --reload --port 8000

# Lint code
uv run ruff check backend/

# Format code
uv run ruff format backend/

# Run tests (when available)
uv run pytest
```

The application runs at http://localhost:8000 with API docs at http://localhost:8000/docs

### Environment Setup
Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`.

## Architecture Overview

This is a RAG (Retrieval-Augmented Generation) system for querying course materials. The architecture follows a tool-based approach where Claude decides when to search the vector store.

### Request Flow

1. **Frontend** (`frontend/`) - Vanilla JS sends queries to `/api/query`
2. **FastAPI** (`backend/app.py`) - Routes to RAG system with session management
3. **RAG Orchestrator** (`backend/rag_system.py`) - Coordinates all components
4. **AI Generator** (`backend/ai_generator.py`) - Calls Claude with tool definitions
5. **Tool Execution** (`backend/search_tools.py`) - Claude invokes `search_course_content`
6. **Vector Store** (`backend/vector_store.py`) - ChromaDB semantic search
7. **Response** flows back through AI → Backend → Frontend with sources

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **RAGSystem** | `rag_system.py` | Main orchestrator; initializes all subsystems |
| **DocumentProcessor** | `document_processor.py` | Parses course docs (txt/pdf/docx), extracts metadata, chunks content with sentence-based overlap |
| **VectorStore** | `vector_store.py` | ChromaDB wrapper; two collections: `course_catalog` (metadata) and `course_content` (chunks) |
| **AIGenerator** | `ai_generator.py` | Claude API client with tool calling support |
| **ToolManager/CourseSearchTool** | `search_tools.py` | Tool interface for Claude; executes semantic search |
| **SessionManager** | `session_manager.py` | In-memory conversation history (not persisted) |

### Document Format

Course documents in `docs/` follow this structure:
```
Line 1: Course Title: [title]
Line 2: Course Link: [url]
Line 3: Course Instructor: [name]
Lesson N: [lesson title]
Lesson Link: [url] (optional)
[lesson content...]
```

The processor extracts lessons, chunks content by sentence (configurable `CHUNK_SIZE`, `CHUNK_OVERLAP`), and prefixes chunks with course/lesson context.

### Tool-Based Search Pattern

Claude is passed a `search_course_content` tool with parameters: `query` (required), `course_name` (optional), `lesson_number` (optional). The AI autonomously decides when to search based on the user's question. This is more flexible than always-retrieving RAG patterns.

### Configuration

All settings in `backend/config.py`:
- `CHUNK_SIZE`: 800, `CHUNK_OVERLAP`: 100
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2
- `MAX_RESULTS`: 5, `MAX_HISTORY`: 2
- `CHROMA_PATH`: `./chroma_db`

### Important Notes

- **No persistence**: Sessions are in-memory only; restarting server clears conversation history
- **Course deduplication**: `add_course_folder()` checks existing course titles to skip re-processing
- **Two-step search**: Course names are resolved semantically via `course_catalog` collection before searching content
- **Sources tracking**: `ToolManager` captures sources from search for display in frontend
