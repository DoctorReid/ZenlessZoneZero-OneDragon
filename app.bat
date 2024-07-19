@echo off

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (

goto UACPrompt

) else ( goto gotAdmin )

:UACPrompt

echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"

echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"

"%temp%\getadmin.vbs"

exit /B

:gotAdmin

if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
chcp 65001

call %~dp0/env.bat

set PYTHONPATH=%~dp0/src

echo 启动中...大约需要10+秒

start "zzz-od-app" %PYTHON% %~dp0/src/zzz_od/gui/app.py > %~dp0/.log/bat.log

timeout /t 10

exit 0
