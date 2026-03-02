@echo off
REM Quick lint script - checks code quality without modifying files
REM Usage: scripts\lint.bat [--fix]

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

if "%~1"=="--fix" (
    echo Running ruff lint with auto-fix...
    uv run ruff check backend/ --fix
) else (
    echo Running ruff lint...
    uv run ruff check backend/
)
echo Done!