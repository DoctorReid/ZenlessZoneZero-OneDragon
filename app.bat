@echo off
chcp 65001
call :initialize

call :createLogFileDir
call :deleteOldLogFiles
call :generateLogFileName

call :checkPythonPath
call :checkPythonPathDir
call :checkAppScriptPath

echo "启动中...大约需要10+秒"
"%PYTHON%" "%PYTHONPATH%\zzz_od\gui\app.py" >> "%BAT_LOG%" 2>&1
if %errorlevel% neq 0 (
    echo "运行出错 请将错误信息反馈 %BAT_LOG%"
    pause
    exit /b 1
)
exit 0

:initialize
call %~dp0env.bat
set "PYTHONPATH=%~dp0src"
echo PYTHON=%PYTHON%
echo PYTHONPATH=%PYTHONPATH%
exit /b

:createLogFileDir
if not exist "%~dp0.log" (
    mkdir "%~dp0.log"
)
exit /b

:deleteOldLogFiles
for /r "%~dp0.log" %%F in (bat_*.log) do (
    del "%%F"
    echo 删除旧日志文件: %%F
)
exit /b

:generateLogFileName
for /f "tokens=1-3 delims=/: " %%i in ('"echo %time%"') do (
    set hour=%%i
    set minute=%%j
    set second=%%k
)
set hour=%hour: =0%
set minute=%minute: =0%
set second=%second: =0%
set timestamp=%hour%.%minute%.%second%
set "BAT_LOG=%~dp0.log\bat_%timestamp%.log"
exit /b

:checkPythonPath
if not exist "%PYTHON%" (
    echo "未配置Python.exe"
    pause
    exit /b 1
)
exit /b

:checkPythonPathDir
if not exist "%PYTHONPATH%" (
    echo "PYTHONPATH 未设置"
    pause
    exit /b 1
)
exit /b

:checkAppScriptPath
if not exist "%PYTHONPATH%\zzz_od\gui\app.py" (
    echo "PYTHONPATH 设置错误 无法找到 %PYTHONPATH%\zzz_od\gui\app.py"
    pause
    exit /b 1
)
exit /b