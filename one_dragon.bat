@echo off
chcp 65001

set "MAINPATH=zzz_od\application\zzz_one_dragon_app.py"

call python_run.bat

timeout /t 10

exit 0