@echo off
chcp 65001

REM 检查是否以管理员权限运行
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    if "%~1"=="-AdminRequest" (
        echo 请求管理员权限失败 尝试不使用管理员运行 脚本运行可能无反应
    ) else (
        echo 请求管理员权限中...
        echo %AdminRequest%
        powershell start-process "%~f0" -verb runas -ArgumentList '-AdminRequest'
        exit /b
    )
) else (
    echo 已获取管理员权限
)

set "MAINPATH=zzz_od\gui\app.py"

call python_run.bat

timeout /t 10

exit 0