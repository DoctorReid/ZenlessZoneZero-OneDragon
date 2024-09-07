import os
import sys
import subprocess
import datetime
import time
import yaml
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

# 设置当前工作目录
path = os.path.dirname(sys.argv[0])
os.chdir(path)

def print_message(message, level="INFO"):
    # 打印消息，带有时间戳和日志级别
    delay(0.1)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    colors = {"INFO": Fore.CYAN, "ERROR": Fore.YELLOW + Style.BRIGHT, "PASS": Fore.GREEN}
    color = colors.get(level, Fore.WHITE)
    print(f"{timestamp} | {color}{level}{Style.RESET_ALL} | {message}")

def delay(seconds):
    # 暂停指定的秒数
    time.sleep(seconds)

def verify_path_issues():
    # 验证路径是否存在问题
    if any('\u4e00' <= char <= '\u9fff' for char in path):
        print_message("路径包含中文字符", "ERROR")
        sys.exit(1)
    if ' ' in path:
        print_message("路径中存在空格", "ERROR")
        sys.exit(1)
    print_message("目录核验通过", "PASS")

def load_yaml_config(file_path):
    # 读取 YAML 配置文件
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print_message(f"读取 YAML 文件错误：{e}", "ERROR")
        sys.exit(1)

def get_python_path_from_yaml(yaml_file_path):
    # 从 YAML 文件中获取 Python 可执行文件路径
    print_message("读取 YAML 文件中...", "INFO")
    config = load_yaml_config(yaml_file_path)
    print_message("YAML 文件读取成功", "PASS")
    print_message("开始配置环境变量...", "INFO")
    python_path = config.get('python_path')
    if not python_path:
        print_message("获取 python_path 失败，请检查路径设置。", "ERROR")
        sys.exit(1)
    return python_path

def configure_environment():
    # 配置环境变量
    yaml_file_path = os.path.join(path, "config", "env.yml")
    python_executable_path = get_python_path_from_yaml(yaml_file_path)
    if not os.path.exists(python_executable_path):
        print_message("未找到 Python 可执行文件，请检查路径设置。", "ERROR")
        sys.exit(1)
    os.environ.update({
        'PYTHON': python_executable_path,
        'PYTHONPATH': os.path.join(path, "src"),
        'PYTHONUSERBASE': os.path.join(path, ".env")
    })
    for var in ['PYTHON', 'PYTHONPATH', 'PYTHONUSERBASE']:
        if not os.environ.get(var):
            print_message(f"{var} 未设置", "ERROR")
            sys.exit(1)
    print_message(f"PYTHON：{os.environ['PYTHON']}", "PASS")
    print_message(f"PYTHONPATH：{os.environ['PYTHONPATH']}", "PASS")
    print_message(f"PYTHONUSERBASE：{os.environ['PYTHONUSERBASE']}", "PASS")

def create_log_folder():
    # 创建日志文件夹
    print_message("开始配置日志...", "INFO")
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    log_folder = os.path.join(path, ".log", date_str)
    os.makedirs(log_folder, exist_ok=True)
    print_message(f"日志文件夹路径：{log_folder}", "PASS")
    return log_folder

def clean_old_logs(log_folder):
    # 删除旧的日志文件
    for root, _, files in os.walk(log_folder):
        for file in files:
            if file.startswith('bat_') and file.endswith('.log'):
                os.remove(os.path.join(root, file))
                print_message(f"已删除旧日志文件: {file}", "PASS")

def execute_python_script(log_folder):
    # 执行 Python 脚本并重定向输出到日志文件
    timestamp = datetime.datetime.now().strftime("%H.%M")
    log_file_path = os.path.join(log_folder, f"python_{timestamp}.log")
    python_executable = os.environ.get('PYTHON')
    app_script_path = os.path.join(os.environ.get('PYTHONPATH'), "zzz_od", "gui", "app.py")

    if not os.path.exists(app_script_path):
        print_message(f"PYTHONPATH 设置错误，无法找到 {app_script_path}", "ERROR")
        sys.exit(1)

    # 使用 PowerShell 启动 Python 脚本并重定向输出
    powershell_command = (
        f"Start-Process '{python_executable}' -ArgumentList '{app_script_path}' -NoNewWindow -RedirectStandardOutput '{log_file_path}' -PassThru"
    )
    # 使用 subprocess.Popen 启动新的 PowerShell 窗口并执行命令
    subprocess.Popen(["powershell", "-Command", powershell_command], creationflags=subprocess.CREATE_NO_WINDOW)
    print_message("绝区零一条龙 正在启动中，大约 5+ 秒...", "INFO")

def main():
    # 主函数
    try:
        print_message(f"当前工作目录：{path}", "INFO")
        verify_path_issues()
        configure_environment()
        log_folder = create_log_folder()
        clean_old_logs(log_folder)
        execute_python_script(log_folder)
    except SystemExit as e:
        print_message(f"程序已退出，状态码：{e.code}", "ERROR")
    except Exception as e:
        print_message(f"出现未处理的异常：{e}", "ERROR")
    finally:
        time.sleep(5)

if __name__ == "__main__":
    main()
