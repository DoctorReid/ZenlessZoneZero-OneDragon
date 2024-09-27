import os.path

import shutil
from typing import Optional, Callable, Tuple

from one_dragon.envs.env_config import DEFAULT_ENV_PATH, DEFAULT_PYTHON_DIR_PATH, EnvConfig, \
    DEFAULT_VENV_DIR_PATH, DEFAULT_VENV_PYTHON_PATH, DEFAULT_PYTHON_PATH
from one_dragon.envs.git_service import GitService
from one_dragon.envs.project_config import ProjectConfig
from one_dragon.utils import file_utils, cmd_utils, os_utils
from one_dragon.utils.log_utils import log


class PythonService:

    def __init__(self, project_config: ProjectConfig, env_config: EnvConfig, git_service: GitService):
        self.project_config = project_config
        self.env_config = env_config
        self.git_service: GitService = git_service

    def install_default_python(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        安装默认的python
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        if self.get_python_version() == self.project_config.python_version:
            log.info('已经安装了推荐版本的python')
            return True
        log.info('开始安装 python')
        for _ in range(2):
            zip_file_name = f'python-{self.project_config.python_version}-embed-amd64.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.git_service.download_env_file(zip_file_name, zip_file_path,
                                                             progress_callback=progress_callback)
                if not success:
                    return False  # 下载失败的 直接返回失败 不重试
            msg = f'开始解压 {zip_file_name}'
            log.info(msg)
            if progress_callback:
                progress_callback(-1, msg)
            success = file_utils.unzip_file(zip_file_path, DEFAULT_PYTHON_DIR_PATH)
            msg = '解压成功' if success else '解压失败 准备重试'
            log.info(msg)
            if progress_callback:
                progress_callback(1 if success else 0, msg)

            if not success:  # 解压失败的话 可能是之前下的zip包坏了 尝试删除重来
                os.remove(zip_file_path)
                continue
            else:
                pth_path = os.path.join(DEFAULT_PYTHON_DIR_PATH, 'python311._pth')
                with open(pth_path, 'a') as file:
                    file.write('\nLib\\site-packages\n')
                return True

        # 重试之后还是失败了
        return False

    def is_virtual_python(self) -> bool:
        """
        是否虚拟环境的python
        :return:
        """
        is_virtual_str = cmd_utils.run_command([self.env_config.python_path, "-c", "import sys; print(getattr(sys, 'base_prefix', sys.prefix) != sys.prefix)"])
        if is_virtual_str is None:
            return False
        else:
            return is_virtual_str == 'True'

    def install_default_pip(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        安装默认的pip，需要先安装了python
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        if self.get_pip_version() is not None:
            log.info('已经安装了pip')
            return True
        log.info('开始安装 pip')
        python_path = self.env_config.python_path
        for _ in range(2):
            py_file_name = 'get-pip.py'
            py_file_path = os.path.join(DEFAULT_ENV_PATH, py_file_name)
            if not os.path.exists(py_file_path):
                success = self.git_service.download_env_file(py_file_name, py_file_path,
                                                             progress_callback=progress_callback)
                if not success:  # 下载失败的 直接返回失败 不重试
                    return False

            if progress_callback:
                progress_callback(-1, '正在安装pip')
            result = cmd_utils.run_command([python_path, py_file_path, '--index-url', self.env_config.pip_source])
            success = result is not None
            msg = '安装pip成功' if success else '安装pip失败 准备重试'
            log.info(msg)
            if progress_callback:
                progress_callback(1 if success else 0, msg)
            if not success:
                # 安装失败的话 可能是之前下的文件坏了 尝试删除重来
                os.remove(py_file_path)
                continue
            else:
                return True

        # 重试之后还是失败了
        return False

    def install_default_virtualenv(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        安装默认的virtualenv，需要先安装了pip
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        if progress_callback:
            progress_callback(-1, '正在安装virtualenv')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'pip', 'install', 'virtualenv', '--index-url', self.env_config.pip_source])
        success = result is not None
        msg = '安装virtualenv成功' if success else '安装virtualenv失败'
        log.info(msg)
        if progress_callback:
            progress_callback(1 if success else 0, msg)
        return success

    def create_default_venv(self, progress_callback: Optional[Callable[[float, str], None]]):
        """
        创建默认的虚拟环境
        :param progress_callback:
        :return:
        """
        if progress_callback:
            progress_callback(-1, '准备创建虚拟环境')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'virtualenv', DEFAULT_VENV_DIR_PATH, '--always-copy'])
        success = result is not None
        msg = '创建虚拟环境成功' if success else '创建虚拟环境失败'
        log.info(msg)
        if progress_callback:
            progress_callback(1 if success else 0, msg)
        return success

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
        python_path = self.env_config.python_path
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
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '-m', 'pip', '--version'])  # Ex: pip 24.0 from xxxx
        if version is not None:
            return version[4: version.find('from') - 1]
        else:
            return None

    def install_default_python_venv(self, progress_callback: Optional[Callable[[float, str], None]]) -> Tuple[bool, str]:
        """
        完整流程安装 python 环境
        :param progress_callback:
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '正在清理旧文件')
        self.env_config.python_path = ''
        if os.path.exists(DEFAULT_PYTHON_DIR_PATH):
            shutil.rmtree(DEFAULT_PYTHON_DIR_PATH)

        if os.path.exists(DEFAULT_VENV_DIR_PATH):
            shutil.rmtree(DEFAULT_VENV_DIR_PATH)

        if not self.install_default_python(progress_callback):
            return False, '安装Python失败'
        self.env_config.python_path = DEFAULT_PYTHON_PATH
        if not self.install_default_pip(progress_callback):
            return False, '安装pip失败'
        if not self.install_default_virtualenv(progress_callback):
            return False, '安装virtualenv失败'
        if not self.create_default_venv(progress_callback):
            return False, '创建虚拟环境失败'
        self.env_config.python_path = DEFAULT_VENV_PYTHON_PATH

        return True, ''

    def install_requirements(self, progress_callback: Optional[Callable[[float, str], None]]) -> Tuple[bool, str]:
        """
        安装依赖
        :return:
        """
        progress_callback(-1, '正在安装...安装过程需要5~10分钟，请耐心等待')

        # 部分人不升级pip会安装失败 不知道为什么
        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade', 'pip',
                                        '--index-url', self.env_config.pip_source])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        if not success:
            return success, msg

        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade',
                                        '-r', os.path.join(os_utils.get_work_dir(), self.project_config.requirements),
                                        '--index-url', self.env_config.pip_source])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        return success, msg

    def get_module_version(self) -> Optional[str]:
        """
        :return: 当前使用的pip版本
        """
        log.info('检测当前pip版本')
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '-m', 'pip', '--version'])  # Ex: pip 24.0 from xxxx
        if version is not None:
            return version[4: version.find('from') - 1]
        else:
            return None