import os
import subprocess

from one_dragon.utils import os_utils, cmd_utils


def start_one_dragon(restart: bool):
    """
    启动一条龙脚本
    :param restart: 是否重启
    :return: 是否成功
    """
    if restart:
        pass

    bat_path = os.path.join(os_utils.get_work_dir(), 'app.bat')
    subprocess.Popen(f'cmd /c "start "zzz-od-runner" "{bat_path}""',
                     shell=True)


if __name__ == '__main__':
    start_one_dragon(True)
