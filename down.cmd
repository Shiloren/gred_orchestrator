@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

call scripts\dev\down.cmd %*
exit /b %ERRORLEVEL%
