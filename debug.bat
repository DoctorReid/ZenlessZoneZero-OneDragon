@echo off
chcp 65001 >nul 2>&1

rem 检查是否以管理员权限运行
net session  >nul 2>&1
if %errorlevel% neq 0 (
    echo -------------------------------
    echo 尝试获取管理员权限中...
    echo -------------------------------
    rem 增加延迟时间，如遇无限循环，则可在此终止程序运行
    timeout /t 2
    PowerShell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

rem 检查路径是否包含中文或空格
powershell -command "if ('%~dp0' -match '[\u4e00-\u9fff]') { exit 1 } else { exit 0 }"
if %errorlevel% equ 1 echo [WARN] 当前路径包含中文字符

set "path_check=%~dp0"
if "%path_check%" neq "%path_check: =%" echo [WARN] 路径中包含空格

:MENU
echo -------------------------------
echo 正在以管理员权限运行...
echo -------------------------------
echo.&echo 1. 强制配置 Python 环境&echo 2. 添加 Git 安全目录&echo 3. 重新安装 Pyautogui 库&echo 4. 检查 PowerShell 路径&echo 5. 重新创建虚拟环境 &echo 6. 重新安装PIP及VIRTUALENV&echo 7. 安装onnxruntime&echo 8. 以DEBUG模式运行一条龙&echo 9. 退出
echo.
set /p choice=请输入选项数字并按 Enter：

if "%choice%"=="1" goto :CONFIG_PYTHON_ENV
if "%choice%"=="2" goto :ADD_GIT_SAFE_DIR
if "%choice%"=="3" goto :REINSTALL_PY_LIBS
if "%choice%"=="4" goto :CHECK_PS_PATH
if "%choice%"=="5" goto :VENV
if "%choice%"=="6" goto :PIP
if "%choice%"=="7" goto :ONNX
if "%choice%"=="8" goto :DEBUG
if "%choice%"=="9" exit /b
echo [ERROR] 无效选项，请重新选择。

goto :MENU

:CONFIG_PYTHON_ENV
echo -------------------------------
echo 正在配置 Python 环境...
echo -------------------------------

set "MAINPATH=zzz_od\gui\app.py"
set "ENV_DIR=%~dp0.env"

rem 调用环境配置脚本
call "%~dp0env.bat"
setx "PYTHON" "%~dp0.env\venv\scripts\python.exe"
setx "PYTHONPATH" "%~dp0src"
setx "PYTHONUSERBASE" "%~dp0.env"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

if not exist "%PYTHON%" echo [WARN] 未配置Python.exe & pause & exit /b 1
if not exist "%PYTHONPATH%" echo [WARN] PYTHONPATH 未设置 & pause & exit /b 1
if not exist "%PYTHONUSERBASE%" echo [WARN] PYTHONUSERBASE 未设置 & pause & exit /b 1
if not exist "%APPPATH%" echo [WARN] PYTHONPATH 设置错误 无法找到 %APPPATH% & pause & exit /b 1

goto :END

:ADD_GIT_SAFE_DIR
echo -------------------------------
echo 尝试添加 Git 安全目录...
echo -------------------------------
setlocal enabledelayedexpansion
set "GIT_PATH=%~dp0.env\PortableGit\bin\git.exe"
set "DIR_PATH=%~dp0"
set "DIR_PATH=%DIR_PATH:\=/%"
set "DIR_PATH=%DIR_PATH:\\=/%"
if "%DIR_PATH:~-1%"=="/" set "DIR_PATH=%DIR_PATH:~0,-1%"
"%GIT_PATH%" config --global --add safe.directory %DIR_PATH%
if %errorlevel% neq 0 echo [ERROR] 添加失败  & pause & exit /b 1
echo [PASS] Git 安全目录添加成功

goto :END

:REINSTALL_PY_LIBS
echo -------------------------------
echo 重新安装 Pyautogui 库...
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

if not exist "%PYTHON%" echo [WARN] 未配置Python.exe & pause & exit /b 1
if not exist "%PYTHONPATH%" echo [WARN] PYTHONPATH 未设置 & pause & exit /b 1
if not exist "%PYTHONUSERBASE%" echo [WARN] PYTHONUSERBASE 未设置 & pause & exit /b 1
if not exist "%APPPATH%" echo [WARN] PYTHONPATH 设置错误 无法找到 %APPPATH% & pause & exit /b 1

%PYTHON% -m pip uninstall pyautogui -y
%PYTHON% -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple pyautogui
%PYTHON% -m pip uninstall pygetwindow -y
%PYTHON% -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple pygetwindow

echo 安装完成...

goto :END

:CHECK_PS_PATH
echo -------------------------------
echo 检查并添加 PowerShell 路径...
echo -------------------------------

set PS_PATH=C:\Windows\System32\WindowsPowerShell\v1.0\
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo PowerShell路径未找到，正在尝试添加...
    setx PATH "%PATH%;C:\Windows\System32\WindowsPowerShell\v1.0\"
    echo PowerShell路径已添加到系统路径中...
) else (
    echo PowerShell路径已存在
)

goto :END

:VENV
echo -------------------------------
echo 重新创建虚拟环境...
echo -------------------------------

set "PYTHON=%~dp0.env\python\python.exe"

if not exist "%PYTHON%" (
    echo [WARN] 未配置Python.exe
    pause
    exit /b 1
)

%PYTHON% -m virtualenv "%~dp0.env\venv" --always-copy

set "input_file=%~dp0config\env.yml"
set "replace_text=python_path: %~dp0.env\venv\scripts\python.exe"

REM 使用 PowerShell 修改 YAML 文件
powershell -Command "(Get-Content '%input_file%') -replace '^(python_path:).*', '%replace_text%' | Set-Content '%input_file%'"

echo 创建虚拟环境完成...

goto :END

:PIP
echo -------------------------------
echo 重新安装 PIP 及 VIRTUALENV库...
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\python\python.exe"

if not exist "%PYTHON%" echo [WARN] 未配置Python.exe & pause & exit /b 1

%PYTHON% %~dp0get-pip.py
%PYTHON% -m pip install virtualenv --index-url https://pypi.tuna.tsinghua.edu.cn/simple
echo 安装完成...

goto :END

:ONNX
echo -------------------------------
echo 安装onnxruntime
echo -------------------------------

call "%~dp0env.bat"

set "PYTHON=%~dp0.env\venv\scripts\python.exe"

if not exist "%PYTHON%" echo [WARN] 未配置Python.exe & pause & exit /b 1

%PYTHON% -m pip install onnxruntime==1.18.0 --index-url https://pypi.tuna.tsinghua.edu.cn/simple


echo 安装完成...

goto :END

:DEBUG
set "MAINPATH=zzz_od\gui\app.py"
set "ENV_DIR=%~dp0.env"

rem 调用环境配置脚本
call "%~dp0env.bat"
set "PYTHON=%~dp0.env\venv\scripts\python.exe"
set "PYTHONPATH=%~dp0src"
set "APPPATH=%PYTHONPATH%\%MAINPATH%"
set "PYTHONUSERBASE=%~dp0.env"

rem 打印信息
echo [PASS] PYTHON：%PYTHON%
echo [PASS] PYTHONPATH：%PYTHONPATH%
echo [PASS] APPPATH：%APPPATH%
echo [PASS] PYTHONUSERBASE：%PYTHONUSERBASE%

rem 检查 Python 可执行文件路径
if not exist "%PYTHON%" (
    echo [WARN] 未配置Python.exe
    pause
    exit /b 1
)

rem 检查 PythonPath 目录
if not exist "%PYTHONPATH%" (
    echo [WARN] PYTHONPATH 未设置
    pause
    exit /b 1
)

rem 检查 PythonUserBase 目录
if not exist "%PYTHONUSERBASE%" (
    echo [WARN] PYTHONUSERBASE 未设置
    pause
    exit /b 1
)

rem 检查应用程序脚本路径
if not exist "%APPPATH%" (
    echo [WARN] PYTHONPATH 设置错误 无法找到 %APPPATH%
    pause
    exit /b 1
)

echo [INFO]启动中...切换到DEBUG模式

%PYTHON% %APPPATH%

goto :END

:END
echo 操作已完成。
pause
cls
goto :MENU
