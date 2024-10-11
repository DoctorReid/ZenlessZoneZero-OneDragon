import os
import subprocess
from typing import List, Optional, Callable
import threading

from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


def run_command(commands: List[str], cwd: Optional[str] = None,
                message_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """
    执行命令行
    :param commands: 需要执行的命令
    :param cwd: 命令的执行目录
    :param message_callback: 命令行日志的回调
    :return 执行结果的 stdout
    """
    command_str = ' '.join(commands)
    log.info(command_str)
    if message_callback is not None:
        message_callback(command_str)
    if cwd is None:  # 这个不写在入参默认值中 防止后续函数返回值会变
        cwd = os_utils.get_work_dir()

    try:
        # 在Windows上
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # 为子进程指定不创建新窗口的标志
        creationflags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(commands, cwd=cwd,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
                                   text=True,
                                   encoding='utf-8',  # 指定编码为 GBK
                                   errors='ignore',  # 忽略解码错误
                                   startupinfo=startupinfo,
                                   creationflags=creationflags
                                   )

        result_str: str = ''

        def read_pipe(pipe, log_func):
            nonlocal result_str
            for line in iter(pipe.readline, ''):
                line_strip = line.strip().strip('"')
                if len(line_strip) == 0:
                    continue
                log_func(line_strip)
                if message_callback is not None:
                    message_callback(line_strip)
                result_str = result_str + '\n' + line_strip

        # 创建两个线程分别处理 stdout 和 stderr
        stdout_thread = threading.Thread(target=read_pipe, args=(process.stdout, log.info))
        stderr_thread = threading.Thread(target=read_pipe, args=(process.stderr, log.error))

        # 启动线程
        stdout_thread.start()
        stderr_thread.start()

        # 等待线程结束
        stdout_thread.join()
        stderr_thread.join()

        # 等待子进程完成
        process.wait()

        if process.returncode == 0:
            return result_str.strip()
        else:
            return None
    except Exception:
        log.error("执行命令失败", exc_info=True)
        return None


def shutdown_sys(seconds: int):
    """
    使用 shutdown -s -t ${seconds} 来关闭系统
    :param seconds: 秒
    :return:
    """
    os.system("shutdown /s /t %d" % seconds)


def cancel_shutdown_sys():
    """
    取消计划的自动关机
    使用 shutdown /a 命令
    :return:
    """
    os.system("shutdown /a")


if __name__ == '__main__':
    run_command(['taskkill', '/F', '/IM', 'git.exe'])
