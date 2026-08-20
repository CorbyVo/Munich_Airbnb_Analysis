@echo off
setlocal

set PROJECT_DIR=D:\PycharmProjects\Munich_Airbnb_Analysis
set PIPELINE_MODE=%1

if "%PIPELINE_MODE%"=="" (
    set PIPELINE_MODE=--skip-download
)

cd /d "%PROJECT_DIR%"

echo Running Munich Airbnb pipeline...
echo Mode: %PIPELINE_MODE%

py scripts\run_pipeline.py %PIPELINE_MODE%

if errorlevel 1 (
    echo Pipeline failed.
    exit /b 1
)

echo Pipeline finished successfully.
endlocal