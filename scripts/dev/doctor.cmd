@echo off
setlocal EnableDelayedExpansion

TITLE GIMO Dev Doctor

set "ROOT_DIR=%~dp0..\.."
cd /d "%ROOT_DIR%" || (echo [ERROR] No se pudo entrar al repo root & exit /b 1)

echo.
echo =======================================================
echo   GIMO Dev Doctor
echo =======================================================

set "FAIL=0"

call :check_tool git "git --version"
call :check_tool node "node --version"
call :check_tool npm "npm --version"
call :check_tool python "python --version"

if exist ".venv\Scripts\python.exe" (
  echo [OK] .venv detectado
) else (
  echo [WARN] .venv no existe. Ejecuta bootstrap.cmd
)

if exist ".env" (
  echo [OK] .env presente
) else (
  echo [WARN] .env ausente. Ejecuta bootstrap.cmd
)

if exist "tools\orchestrator_ui\.env.local" (
  echo [OK] tools\orchestrator_ui\.env.local presente
) else (
  echo [WARN] tools\orchestrator_ui\.env.local ausente
)

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:9325/auth/check' -TimeoutSec 2; Write-Output ('[OK] Backend responde en 9325 (HTTP ' + $r.StatusCode + ')') } catch { Write-Output '[INFO] Backend no responde en 9325 (normal si no esta iniciado)' }"

echo.
echo [DONE] Doctor finalizado.
if "%FAIL%"=="1" (
  echo [ACTION] Faltan herramientas base. Instala prerequisitos y reintenta.
  exit /b 1
)
exit /b 0

:check_tool
set "TOOL_NAME=%~1"
set "TOOL_CMD=%~2"
where %TOOL_NAME% >nul 2>&1
if errorlevel 1 (
  echo [ERROR] %TOOL_NAME% no esta en PATH
  set "FAIL=1"
  goto :eof
)
for /f "delims=" %%V in ('%TOOL_CMD% 2^>nul') do (
  echo [OK] %%V
  goto :eof
)
echo [OK] %TOOL_NAME% detectado
goto :eof
