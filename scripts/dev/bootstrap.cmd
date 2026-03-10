@echo off
setlocal EnableDelayedExpansion

rem Evita que un venv roto heredado rompa la deteccion de Python en nuevas consolas
set "VIRTUAL_ENV="
set "PYTHONHOME="
set "PYTHONPATH="

TITLE GIMO Bootstrap

set "ROOT_DIR=%~dp0..\.."
cd /d "%ROOT_DIR%" || (echo [ERROR] No se pudo entrar al repo root & exit /b 1)

echo.
echo =======================================================
echo   GIMO Bootstrap ^(Portable Dev Setup^)
echo =======================================================

where git >nul 2>&1 || (echo [ERROR] git no esta en PATH & exit /b 1)
where npm >nul 2>&1 || (echo [ERROR] npm no esta en PATH & exit /b 1)

set "PY_BOOTSTRAP="
set "SYS_PY_VER="
set "SYS_PY_MAJOR="

where py >nul 2>&1
if not errorlevel 1 (
  py -3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" >nul 2>&1
  if not errorlevel 1 set "PY_BOOTSTRAP=py -3.11"
  if not defined PY_BOOTSTRAP (
    py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" >nul 2>&1
    if not errorlevel 1 (
      set "PY_BOOTSTRAP=py -3"
      for /f %%V in ('py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "SYS_PY_VER=%%V"
      echo [WARN] Python 3.11 no detectado. Usando Python !SYS_PY_VER! via py launcher.
    )
  )
)

if not defined PY_BOOTSTRAP (
  where python >nul 2>&1 || (
    echo [ERROR] No se encontro Python 3.x en PATH.
    echo         Instala Python 3 y reintenta: https://www.python.org/downloads/
    exit /b 1
  )
  for /f %%V in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "SYS_PY_VER=%%V"
  for /f %%V in ('python -c "import sys; print(sys.version_info.major)"') do set "SYS_PY_MAJOR=%%V"
  if "!SYS_PY_MAJOR!"=="3" (
    set "PY_BOOTSTRAP=python"
  )
)

if not defined PY_BOOTSTRAP (
  echo [ERROR] Python 3.x no disponible.
  echo         Version detectada de 'python': !SYS_PY_VER!
  echo         Instala Python 3 y reintenta bootstrap.
  exit /b 1
)

set "RECREATE_VENV=0"
if exist ".venv\Scripts\python.exe" (
  if not exist ".venv\pyvenv.cfg" set "RECREATE_VENV=1"
  if "!RECREATE_VENV!"=="0" (
    ".venv\Scripts\python.exe" -c "import sys; print(sys.version_info.major)" >nul 2>&1
    if errorlevel 1 set "RECREATE_VENV=1"
  )

  if "!RECREATE_VENV!"=="1" (
    echo [WARN] .venv corrupto/incompleto detectado. Recreando entorno virtual...
    rmdir /s /q ".venv" >nul 2>&1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/8] Creando entorno virtual .venv ...
  %PY_BOOTSTRAP% -m venv .venv || (echo [ERROR] No se pudo crear .venv & exit /b 1)
)
set "PYTHON_EXE=.venv\Scripts\python.exe"

echo [2/8] Actualizando pip/setuptools/wheel ...
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel >nul 2>&1

echo [3/8] Instalando dependencias Python ...
"%PYTHON_EXE%" -m pip install -r requirements.txt || (echo [ERROR] Fallo pip install & exit /b 1)

echo [4/8] Instalando dependencias UI ^(npm ci^) ...
pushd tools\orchestrator_ui >nul
npm ci || (popd >nul & echo [ERROR] Fallo npm ci en orchestrator_ui & exit /b 1)
popd >nul

echo [5/8] Instalando dependencias Web ^(npm ci^) ...
pushd apps\web >nul
npm ci || (popd >nul & echo [ERROR] Fallo npm ci en apps/web & exit /b 1)
popd >nul

echo [6/8] Preparando .env ...
if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
)

set "ORCH_TOKEN="
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="ORCH_TOKEN" set "ORCH_TOKEN=%%B"
)

if "!ORCH_TOKEN!"=="" (
  for /f %%T in ('powershell -NoProfile -Command "$bytes = New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes); [Convert]::ToBase64String($bytes)"') do set "ORCH_TOKEN=%%T"
  >> ".env" echo ORCH_TOKEN=!ORCH_TOKEN!
)

echo [7/8] Preparando tools\orchestrator_ui\.env.local ...
(
  echo VITE_API_URL=http://127.0.0.1:9325
  echo VITE_ORCH_TOKEN=!ORCH_TOKEN!
) > "tools\orchestrator_ui\.env.local"

echo [8/8] Registrando MCP server gimo ...
"%PYTHON_EXE%" scripts\setup_mcp.py >nul 2>&1
if errorlevel 1 (
  echo [WARN] setup_mcp.py no pudo completar en este momento. Puedes reintentar luego.
)

echo.
echo [OK] Bootstrap completado.
echo     Siguiente paso: GIMO_DEV_LAUNCHER.cmd
echo.
exit /b 0
