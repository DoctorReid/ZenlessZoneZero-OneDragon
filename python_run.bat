@echo off
chcp 65001

REM 调用环境配置脚本
call "%~dp0env.bat"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
echo PYTHON=%PYTHON%
echo PYTHONPATH=%PYTHONPATH%
echo APPPATH=%APPPATH%

REM 使用 PowerShell 检查路径中是否有中文字符
powershell -command "if ('%~dp0' -match '[\u4e00-\u9fff]') { exit 1 } else { exit 0 }"
if %errorlevel% equ 1 (
    echo 警告：当前路径包含中文字符
)

REM 检查路径中是否有空格
set "path_check=%~dp0"
if "%path_check%" neq "%path_check: =%" (
    echo 警告：路径中包含空格
)

REM 获取当前日期并格式化为 YYYYMMDD
for /f "tokens=2-4 delims=/ " %%a in ('echo %date%') do (
    set year=%%c
    set month=%%a
    set day=%%b
)

REM 获取当前时间
for /f "tokens=1-3 delims=/: " %%i in ('echo %time%') do (
    set hour=%%i
    set minute=%%j
    set second=%%k
)

REM 将小时和分钟格式化为两位数
set hour=%hour: =0%
set minute=%minute: =0%
set second=%second: =0%

REM 生成日志目录和文件名，格式为 YYYYMMDD 和 HH.MM.SS
set log_dir=%~dp0.log\%year%%month%%day%
set timestamp=%hour%.%minute%.%second%
set "BAT_LOG=%log_dir%\bat_%timestamp%.log"

REM 检查并创建日志目录
if not exist "%log_dir%" (
    echo 日志目录不存在，正在创建...
    mkdir "%log_dir%"
    if %errorlevel% neq 0 (
        echo 创建日志目录失败。
        pause
        exit /b 1
    )
    echo 日志目录创建成功。
)

REM 删除所有以 'bat_' 开头且以 '.log' 结尾的文件
for /r "%log_dir%" %%F in (bat_*.log) do (
    del "%%F"
    echo 删除旧日志文件: %%F
)

REM 检查 Python 可执行文件路径
if not exist "%PYTHON%" (
    echo "未配置Python.exe"
    pause
    exit /b 1
)

REM 检查 PythonPath 目录
if not exist "%PYTHONPATH%" (
    echo "PYTHONPATH 未设置"
    pause
    exit /b 1
)

REM 检查应用程序脚本路径
if not exist "%APPPATH%" (
    echo "PYTHONPATH 设置错误 无法找到 %APPPATH%"
    pause
    exit /b 1
)

echo "启动中...大约需要10+秒"
"%PYTHON%" "%APPPATH%" >> "%BAT_LOG%" 2>&1
if %errorlevel% neq 0 (
    echo "运行出错 请将错误信息反馈 %BAT_LOG%"
    pause
    exit /b 1
)
exit 0
