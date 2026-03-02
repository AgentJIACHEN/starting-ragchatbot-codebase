@echo off
REM Code quality script - runs formatting, linting, and tests
REM Usage: scripts\quality.bat [--fix] [--format] [--lint] [--test]

setlocal enabledelayedexpansion

REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM Parse arguments
set FIX_MODE=false
set RUN_FORMAT=true
set RUN_LINT=true
set RUN_TEST=false

:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--fix" set FIX_MODE=true
if /i "%~1"=="--format-only" (
    set RUN_LINT=false
    set RUN_TEST=false
)
if /i "%~1"=="--lint-only" (
    set RUN_FORMAT=false
    set RUN_TEST=false
)
if /i "%~1"=="--test" set RUN_TEST=true
if /i "%~1"=="--all" set RUN_TEST=true
shift
goto :parse_args
:done_args

echo === Code Quality Checks ===
echo.

REM Format code
if "%RUN_FORMAT%"=="true" (
    echo Running ruff format...
    if "%FIX_MODE%"=="true" (
        uv run ruff format backend/
    ) else (
        uv run ruff format --check backend/
    )
    if !errorlevel! equ 0 (
        echo [OK] Formatting check passed
    ) else (
        if "%FIX_MODE%"=="false" (
            echo Run with --fix to auto-format
        )
    )
    echo.
)

REM Lint code
if "%RUN_LINT%"=="true" (
    echo Running ruff lint...
    if "%FIX_MODE%"=="true" (
        uv run ruff check backend/ --fix
    ) else (
        uv run ruff check backend/
    )
    if !errorlevel! equ 0 (
        echo [OK] Lint check passed
    ) else (
        if "%FIX_MODE%"=="false" (
            echo Run with --fix to auto-fix issues
        )
    )
    echo.
)

REM Run tests
if "%RUN_TEST%"=="true" (
    echo Running pytest...
    uv run pytest backend/tests/ -v
    if !errorlevel! equ 0 (
        echo [OK] All tests passed
    )
    echo.
)

echo === Quality checks complete ===