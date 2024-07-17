@echo off
chcp 65001

call %~dp0/env.bat

set PYTHONPATH=%~dp0/src

echo 启动中...大约需要10+秒

start "zzz-od-app" %PYTHON% %~dp0/src/zzz_od/gui/app.py > %~dp0/.log/bat.log

timeout /t 10

exit 0
