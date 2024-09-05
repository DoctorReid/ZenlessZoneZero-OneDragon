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
"%PYTHON%" "%APPPATH%" >> "%BAT_LOG%" 2>&1
if %errorlevel% neq 0 (
    echo "运行出错 请将错误信息反馈 %BAT_LOG%"
    pause
    exit /b 1
) else (
    echo "运行结束 日志可见 .log/log.txt"
)

goto :end

:initialize
call %~dp0env.bat
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
echo PYTHON=%PYTHON%
echo PYTHONPATH=%PYTHONPATH%
echo APPPATH=%APPPATH%
exit /b

:createLogFileDir
if not exist "%~dp0.log" (
    mkdir "%~dp0.log"
)
exit /b

:deleteOldLogFiles
for /r "%~dp0.log" %%F in (bat_log_*.txt) do (
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
set "BAT_LOG=%~dp0.log\bat_log_%timestamp%.txt"
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
if not exist "%APPPATH%" (
    echo "APPPATH 设置错误 无法找到 %APPPATH%"
    pause
    exit /b 1
)
exit /b

:end