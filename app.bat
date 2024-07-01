@echo off
chcp 65001

call env.bat

set PYTHONPATH=%~dp0src
echo %PYTHONPATH%

start "ZZZ-OD" %PYTHON% src/zzz_od/gui/app.py >nul 2>&1