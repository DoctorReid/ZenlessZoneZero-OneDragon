import os
import sys
import subprocess
import datetime
import time
import yaml
from colorama import init, Fore, Style

'''
此文件使用Nuitka进行打包,使用前需要在终端的python安装nuitka(虚拟环境不行),并cd到一条龙目录中
安装指令：
pip install nuitka
打包指令:
python -m nuitka --standalone --onefile --windows-uac-admin --output-dir=dist --windows-icon-from-ico=assets/ui/zzz_logo.ico app.py && ren "dist\\app.exe" "OneDragon Launcher.exe"
打包后的文件位于dist文件夹内,将其移动到主目录即可
'''

# 初始化 colorama
init(autoreset=True)

# 设置当前工作目录
path = os.path.dirname(sys.argv[0])
os.chdir(path)

def get_formatted_datetime():
    """
    获取并格式化当前日期和时间
    """
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d"), now.strftime("%H.%M")

def print_formatted_message(message, level="INFO"):
    """
    打印格式化的消息，带有时间戳和级别
    """
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    if level == "INFO":
        color = Fore.CYAN
    elif level == "WARN":
        color = Fore.YELLOW
    elif level == "ERROR":
        color = Fore.RED
    elif level == "PASS":
        color = Fore.GREEN
    formatted_message = f"{timestamp} | {color}{level}{Style.RESET_ALL} | {message}"
    print(formatted_message)

def run_command(command):
    """
    执行命令，不打印输出
    """
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def verify_path_issues():
    """
    检查路径中是否存在中文字符或空格
    """
    print_formatted_message("检查路径设置...", "INFO")

    if any('\u4e00' <= char <= '\u9fff' for char in path):
        print_formatted_message("路径包含中文字符", "WARN")
        sys.exit(1)
    
    if ' ' in path:
        print_formatted_message("路径中存在空格", "WARN")
        sys.exit(1)

    print_formatted_message("路径设置正确", "PASS")

def load_yaml_config(file_path):
    """
    读取 YAML 文件并返回配置数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config
    except Exception as e:
        print_formatted_message(f"读取 YAML 文件错误：{e}", "ERROR")
        sys.exit(1)

def get_python_path_from_yaml(yaml_file_path):
    """
    从 YAML 文件中获取 python_path
    """
    config = load_yaml_config(yaml_file_path)
    python_path = config.get('python_path')
    if not python_path:
        print_formatted_message("获取 python_path 失败，请检查路径设置。", "WARN")
        sys.exit(1)
    
    return python_path

def configure_environment():
    """
    配置环境变量并显示设置
    """
    yaml_file_path = os.path.join(path,"config","env.yml")
    print_formatted_message("检查环境变量...", "INFO")
    python_executable_path = get_python_path_from_yaml(yaml_file_path)
    
    if not os.path.exists(python_executable_path):
        print_formatted_message("未找到 Python 可执行文件，请检查路径设置。", "WARN")
        sys.exit(1)  
    
    os.environ['PYTHON'] = python_executable_path

    src_path = os.path.join(path, "src")
    os.environ['PYTHONPATH'] = src_path

    env_path = os.path.join(path, ".env")
    os.environ['PYTHONUSERBASE'] = env_path

    python_executable = os.environ.get('PYTHON')
    python_src_path = os.environ.get('PYTHONPATH')
    python_env_path = os.environ.get('PYTHONUSERBASE')

    print_formatted_message(f"PYTHON：{python_executable}", "PASS")
    print_formatted_message(f"PYTHONPATH：{python_src_path}", "PASS")
    print_formatted_message(f"PYTHONUSERBASE：{python_env_path}", "PASS")

    if not python_executable:
        print_formatted_message("未配置 Python.exe", "WARN")
        sys.exit(1)  

    if not python_src_path:
        print_formatted_message("PYTHONPATH 未设置", "WARN")
        sys.exit(1)  
    
    if not python_env_path:
        print_formatted_message("PYTHONUSERBASE 未设置", "WARN")
        sys.exit(1)  

def create_log_folder():
    """
    创建日志文件夹（如果不存在）
    """
    date_str,_ = get_formatted_datetime()
    print_formatted_message("检索日志文件夹中...", "INFO")
    log_folder = os.path.join(path, ".log", date_str)

    if not os.path.exists(log_folder):
        print_formatted_message("日志文件夹不存在，正在创建...", "WARN")
        try:
            os.makedirs(log_folder)
            print_formatted_message("日志文件夹创建成功。", "PASS")
        except OSError as e:
            print_formatted_message(f"日志文件夹创建失败：{e}", "WARN")
            sys.exit(1)  
    else:
        print_formatted_message(f"日志文件夹路径：{log_folder}", "PASS")
    return log_folder

def clean_old_logs(log_folder):
    """
    删除日志文件夹中的旧日志文件
    """
    print_formatted_message("删除旧日志中...", "INFO")
    for root, _, files in os.walk(log_folder):
        for file in files:
            if file.startswith('bat_') and file.endswith('.log'):
                os.remove(os.path.join(root, file))
                print_formatted_message(f"已删除旧日志文件: {file}", "PASS")

def execute_python_script(log_folder):
    """
    执行 Python 脚本，并将输出写入日志文件
    """
    _, timestamp = get_formatted_datetime()
    log_file_path = os.path.join(log_folder, f"bat_{timestamp}.log")

    python_executable = os.environ.get('PYTHON')
    python_path = os.environ.get('PYTHONPATH')

    app_script_path = os.path.join(python_path, "zzz_od", "gui", "app.py")

    if not os.path.exists(app_script_path):
        print_formatted_message(f"PYTHONPATH 设置错误，无法找到 {app_script_path}", "WARN")
        sys.exit(1)  

    print_formatted_message("启动中...大约需要 10+ 秒", "INFO")
    with open(log_file_path, 'w') as log_file:
        result = subprocess.run([python_executable, app_script_path], stdout=log_file, stderr=subprocess.STDOUT)

    if result.returncode != 0:
        print_formatted_message(f"运行出错，请查看日志：{log_file_path}", "WARN")
        sys.exit(1)  

def main():
    """
    主函数，执行所有步骤
    """
    try:
        time.sleep(0.1)
        print_formatted_message(f"当前工作目录：{path}", "INFO")
        time.sleep(0.1)
        verify_path_issues()
        time.sleep(0.1)
        configure_environment()
        time.sleep(0.1)
        log_folder = create_log_folder()
        time.sleep(0.1)
        clean_old_logs(log_folder)
        time.sleep(0.1)
        execute_python_script(log_folder)
    except SystemExit as e:
        print_formatted_message(f"程序已退出，状态码：{e.code}", "ERROR")
    except Exception as e:
        print_formatted_message(f"出现未处理的异常：{e}", "ERROR")
    finally:
        input("按 Enter 键退出程序...")

if __name__ == "__main__":
    main()
