@echo off
:: =====================================================================
:: GIMO SECURE UNIFIED LAUNCHER (Windows)
:: =====================================================================
:: This script starts both the Python Backend and the React Frontend.
:: Enhanced with: Virtual Env, Port Cleanup, Health Checks.
:: =====================================================================
TITLE GIMO Secure Launcher
setlocal enabledelayedexpansion

:: Colors (if supported)
set "ESC="
set "BLUE=%ESC%[34m"
set "GREEN=%ESC%[32m"
set "RED=%ESC%[31m"
set "YELLOW=%ESC%[33m"
set "RESET=%ESC%[0m"

echo %BLUE%[1/5]%RESET% Preparando entorno...
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 1. Detect Virtual Environment
set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [INFO] Usando entorno virtual: .venv
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
    echo [INFO] Usando entorno virtual: venv
) else (
    echo %YELLOW%[WARN]%RESET% No se detectó .venv o venv. Usando python global.
)

:: 2. Verificar/Generar ORCH_TOKEN
set ENV_FILE=.env
if not exist "%ENV_FILE%" (
    echo [INFO] .env no encontrado. Inicializando...
    echo ORCH_PORT=9325 > "%ENV_FILE%"
)

findstr "ORCH_TOKEN" "%ENV_FILE%" >nul
if errorlevel 1 (
    echo %BLUE%[INFO]%RESET% Generando ORCH_TOKEN de alta entropía...
    for /f %%T in ('powershell -NoProfile -Command "$bytes = New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes); [Convert]::ToBase64String($bytes)"') do set "GENERATED_TOKEN=%%T"
    echo ORCH_TOKEN=!GENERATED_TOKEN!>> "%ENV_FILE%"
    echo %GREEN%[OK]%RESET% Token guardado en %ENV_FILE%
    
    :: Sync token with Frontend (Vite)
    echo VITE_ORCH_TOKEN=!GENERATED_TOKEN!> "tools\orchestrator_ui\.env.local"
    echo %GREEN%[OK]%RESET% Token sincronizado con Frontend (.env.local)
)

:: 3. Limpiar procesos previos
echo %BLUE%[2/5]%RESET% Limpiando puertos 9325 (Backend) y 5173 (Frontend)...
for %%p in (9325 5173) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do (
        echo [INFO] Matando proceso previo %%a en puerto %%p...
        taskkill /F /PID %%a >nul 2>&1
    )
)

:: 4. Lanzar Backend
echo %BLUE%[3/5]%RESET% Lanzando GIMO Backend (127.0.0.1:9325)...
start "GIMO Backend" cmd /c "title GIMO Backend && %PYTHON_EXE% -m uvicorn tools.gimo_server.main:app --host 127.0.0.1 --port 9325 --log-level info"

:: 5. Esperar Backend Health Check
echo %BLUE%[4/5]%RESET% Esperando a que el Backend esté listo...
%PYTHON_EXE% scripts\dev\health_check.py --port 9325 --timeout 30
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% El backend no respondió a tiempo. Revisa la ventana de consola del backend.
    pause
    exit /b 1
)

:: 6. Lanzar Frontend
echo %BLUE%[5/5]%RESET% Iniciando GIMO Frontend (Vite)...
cd tools\orchestrator_ui
start "GIMO Frontend" cmd /c "title GIMO Frontend && npm run dev -- --host 127.0.0.1"

:: 7. Finalizar
echo.
echo %GREEN%[SUCCESS]%RESET% GIMO está operativo! 🚀
echo.
echo  - Backend: http://127.0.0.1:9325
echo  - Frontend: http://127.0.0.1:5173 (Vite Default)
echo.
echo [INFO] Abriendo navegador en 3 segundos...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:5173

echo.
echo [TIP] Puedes cerrar esta ventana.
timeout /t 10
exit

