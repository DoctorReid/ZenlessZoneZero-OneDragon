import os.path
import subprocess
from typing import Optional, Callable

from one_dragon.envs.env_config import env_config, DEFAULT_ENV_PATH, DEFAULT_PYTHON_DIR_PATH
from one_dragon.envs.git_service import git_service
from one_dragon.envs.project_config import project_config
from one_dragon.utils import file_utils, cmd_utils, os_utils
from one_dragon.utils.log_utils import log


class PythonService:

    def __init__(self):
        self.env = env_config
        self.project = project_config
        self.github_service = git_service

    def install_default_python(self, progress_callback: Optional[Callable[[float, str], None]]) -> bool:
        """
        安装默认的python
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        log.info('开始安装 python')
        if self.get_python_version() == self.project.python_version:
            log.info('已经安装了推荐版本的python')
            return True
        for _ in range(2):
            zip_file_name = f'python-{self.project.python_version}-embed-amd64.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.github_service.download_env_file(zip_file_name, zip_file_path,
                                                                progress_callback=progress_callback)
                if not success:
                    return False
            msg = f'开始解压 {zip_file_name}'
            log.info(msg)
            if progress_callback:
                progress_callback(0, msg)
            success = file_utils.unzip_file(zip_file_path, DEFAULT_PYTHON_DIR_PATH)
            msg = '解压成功' if success else '解压失败 准备重试'
            log.info(msg)
            if progress_callback:
                progress_callback(1 if success else 0, msg)

            if not success:  # 解压失败的话 可能是之前下的zip包坏了 尝试删除重来
                os.remove(zip_file_path)
                continue
            else:
                return True

        # 重试之后还是失败了
        return False

    def install_default_pip(self, progress_callback: Optional[Callable[[float, str], None]]) -> bool:
        """
        安装默认的pip，需要先安装了python
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        log.info('开始安装 pip')
        if self.get_pip_version() == self.project.pip_version:
            log.info('已经安装了推荐版本的pip')
            return True
        python_path = self.env.python_path
        for _ in range(2):
            py_file_name = 'get-pip.py'
            py_file_path = os.path.join(DEFAULT_ENV_PATH, py_file_name)
            if not os.path.exists(py_file_path):
                success = self.github_service.download_env_file(py_file_name, py_file_path,
                                                                progress_callback=progress_callback)
                if not success:
                    return False

            result = cmd_utils.run_command([python_path, py_file_path])
            if result is None:
                log.error('安装pip失败 准备重试')
                # 安装失败的话 可能是之前下的文件坏了 尝试删除重来
                os.remove(py_file_path)
                continue
            else:
                return True

        # 重试之后还是失败了
        return False

    def get_os_python_path(self) -> Optional[str]:
        """
        获取当前系统环境变量中的python路径
        :return:
        """
        log.info('获取系统环境变量的python')
        message = cmd_utils.run_command(['where', 'pyhon'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_python_version(self) -> Optional[str]:
        """
        :return: 当前使用的python版本
        """
        log.info('检测当前python版本')
        python_path = self.env.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '--version'])  # Ex: Python 3.11.9
        if version is not None:
            return version[7:]
        else:
            return None

    def get_os_pip_path(self) -> Optional[str]:
        """
        获取当前系统环境变量中的pip路径
        :return:
        """
        log.info('获取系统环境变量的pip')
        message = cmd_utils.run_command(['where', 'pip'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_pip_version(self) -> Optional[str]:
        """
        :return: 当前使用的pip版本
        """
        log.info('检测当前pip版本')
        pip_path = self.env.pip_path
        if pip_path == '' or not os.path.exists(pip_path):
            return None

        version = cmd_utils.run_command([pip_path, '--version'])  # Ex: pip 24.0 from xxxx
        if version is not None:
            return version[4: version.find('from') - 1]
        else:
            return None

    def install_requirements(self, progress_callback: Optional[Callable[[float, str], None]]) -> bool:
        """
        安装依赖
        :return:
        """
        progress_callback(-1, '正在安装')
        result = cmd_utils.run_command([self.env.pip_path, 'install' '-r',
                                        os.path.join(os_utils.get_work_dir(), self.project.requirements)])
        return result is not None


python_service = PythonService()
