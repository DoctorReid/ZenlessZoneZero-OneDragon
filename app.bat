@echo off
chcp 65001
call %~dp0env.bat
set "PYTHONPATH=%~dp0src"
echo PYTHON=%PYTHON%
echo PYTHONPATH=%PYTHONPATH%
if not exist "%~dp0.log" (
    mkdir "%~dp0.log"
)
set "LOGFILE=%~dp0.log\debug.log"

echo PYTHON=%PYTHON% > "%LOGFILE%"
echo PYTHONPATH=%PYTHONPATH% >> "%LOGFILE%"

rem 检查 Python 可执行文件路径
if not exist "%PYTHON%" (
    echo Python executable not found at %PYTHON%
    echo "Python executable not found at %PYTHON%" >> "%LOGFILE%"
    exit /b 1
)

rem 检查 PythonPath 目录
if not exist "%PYTHONPATH%" (
    echo Python path not found at %PYTHONPATH%
    echo "Python path not found at %PYTHONPATH%" >> "%LOGFILE%"
    exit /b 1
)

rem 检查应用程序脚本路径
if not exist "%PYTHONPATH%\zzz_od\gui\app.py" (
    echo Application script not found at %PYTHONPATH%\zzz_od\gui\app.py
    echo "Application script not found at %PYTHONPATH%\zzz_od\gui\app.py" >> "%LOGFILE%"
    exit /b 1
)

echo 启动中...大约需要10+秒
"%PYTHON%" "%PYTHONPATH%\zzz_od\gui\app.py" >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo An error occurred while running the application. Check the debug.log for details.
    echo An error occurred while running the application. >> "%LOGFILE%"
)
timeout /t 10
exit 0
