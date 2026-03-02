@echo off
REM Quick format script - formats all Python files
REM Usage: scripts\format.bat

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

echo Formatting code with ruff...
uv run ruff format backend/
echo Done!