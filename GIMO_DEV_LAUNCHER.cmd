@echo off
setlocal

REM Canonical launcher entrypoint (portable, one-command flow)
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

call scripts\dev\up.cmd %*
exit /b %ERRORLEVEL%
