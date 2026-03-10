@echo off
setlocal

TITLE GIMO Dev Down

set "ROOT_DIR=%~dp0..\.."
cd /d "%ROOT_DIR%" || (echo [ERROR] No se pudo entrar al repo root & exit /b 1)

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [1/2] Cerrando ventanas GIMO...
taskkill /F /FI "WINDOWTITLE eq GIMO Backend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GIMO Frontend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GIMO Web*" /T >nul 2>&1

echo [2/2] Liberando puertos 9325, 5173, 3000...
"%PYTHON_EXE%" scripts\ops\kill_port.py 9325 5173 3000 >nul 2>&1

echo [OK] GIMO detenido y puertos liberados.
exit /b 0
