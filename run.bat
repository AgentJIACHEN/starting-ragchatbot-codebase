@echo off
REM Create necessary directories
if not exist "docs" mkdir docs

REM Check if backend directory exists
if not exist "backend" (
    echo Error: backend directory not found
    exit /b 1
)

echo Starting Course Materials RAG System...
echo Make sure you have set your ANTHROPIC_API_KEY in .env

REM Change to backend directory and start the server
cd backend && uv run uvicorn app:app --reload --port 8000
