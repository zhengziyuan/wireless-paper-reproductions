@echo off
setlocal
chcp 65001 >nul
set "MIS_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%MIS_PYTHON%" set "MIS_PYTHON=python"
"%MIS_PYTHON%" "%~dp0generate.py"
if errorlevel 1 goto failed
"%MIS_PYTHON%" "%~dp0verify.py"
if errorlevel 1 goto failed
echo.
echo MIS data generation and 19 numerical checks completed.
exit /b 0
:failed
echo.
echo Reproduction failed. A Python environment with numpy 2.3.5 is required.
exit /b 1
