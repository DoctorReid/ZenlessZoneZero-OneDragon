import os.path
import time

import re
import shutil
import urllib.parse
from typing import Optional, Callable, Tuple

from one_dragon.envs.env_config import EnvConfig, PipSourceEnum, CpythonSourceEnum, DEFAULT_ENV_PATH, DEFAULT_UV_DIR_PATH,\
     DEFAULT_PYTHON_DIR_PATH, DEFAULT_PYTHON_PATH, DEFAULT_VENV_DIR_PATH, DEFAULT_VENV_PYTHON_PATH
from one_dragon.envs.download_service import DownloadService
from one_dragon.envs.project_config import ProjectConfig
from one_dragon.utils import file_utils, cmd_utils, os_utils
from one_dragon.utils.log_utils import log


class PythonService:

    def __init__(self, project_config: ProjectConfig, env_config: EnvConfig, download_service: DownloadService):
        self.project_config = project_config
        self.env_config = env_config
        self.download_service: DownloadService = download_service

    def install_default_uv(self, progress_callback: Optional[Callable[[float, str], None]]) -> Tuple[bool, str]:
        if self.get_uv_version() is not None:
            msg = '已经安装了 UV'
            log.info(msg)
            return True, msg

        msg = '开始安装 UV'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        for _ in range(2):
            zip_file_name = 'uv-x86_64-pc-windows-msvc.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            download_url = f'https://github.com/astral-sh/uv/releases/latest/download/{zip_file_name}'
            if not os.path.exists(zip_file_path):
                # success = self.download_service.download_env_file(zip_file_name, zip_file_path, progress_callback=progress_callback)
                success = self.download_service.download_file_from_url(download_url, zip_file_path, progress_callback=progress_callback)
                if not success:
                    return False, '下载 UV 失败 请尝试到「设置」更改网络代理'

            msg = f'开始解压 {zip_file_name}'
            log.info(msg)
            if progress_callback is not None:
                progress_callback(0, msg)

            success = file_utils.unzip_file(zip_file_path, DEFAULT_UV_DIR_PATH)

            msg = '解压成功' if success else '解压失败 准备重试'
            log.info(msg)
            if progress_callback is not None:
                progress_callback(1 if success else 0, msg)

            if not success:  # 解压失败的话 可能是之前下的zip包坏了 尝试删除重来
                os.remove(zip_file_path)
                continue
            else:
                return True, '安装 UV 成功'

        # 重试之后还是失败了
        return False, '安装UV失败'

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
                success = self.download_service.download_env_file(zip_file_name, zip_file_path, progress_callback=progress_callback)
                if not success:
                    return False  # 下载失败的 直接返回失败 不重试
            msg = f'开始解压 {zip_file_name}'
            log.info(msg)
            if progress_callback is not None:
                progress_callback(-1, msg)
            success = file_utils.unzip_file(zip_file_path, DEFAULT_PYTHON_DIR_PATH)
            msg = '解压成功' if success else '解压失败 准备重试'
            log.info(msg)
            if progress_callback is not None:
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

    def uv_install_python(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> bool:
        """
        使用uv安装python
        """
        if not self.env_config.uv_path:
            if progress_callback is not None:
                progress_callback(0, '未找到 UV 路径')
            return False

        if progress_callback is not None:
            progress_callback(-1, '开始使用 UV 安装 Python')
        log.info('开始使用 UV 安装 Python')
        source = self.env_config.cpython_source
        if source == CpythonSourceEnum.GITHUB.value.value and self.env_config.is_gh_proxy:
            source = f'{self.env_config.gh_proxy_url}/{source}'
        result = cmd_utils.run_command([self.env_config.uv_path, 'python', 'install', self.project_config.uv_python_version,
                                        '--mirror', self.env_config.cpython_source,
                                        '--install-dir', DEFAULT_PYTHON_DIR_PATH])
        msg = 'UV 安装 Python 成功' if result is not None else 'UV 安装 Python 失败'
        log.info(msg)
        if result is None:
            if progress_callback is not None:
                progress_callback(0, msg)
            return False
        else:
            if progress_callback is not None:
                progress_callback(1, msg)
            return True

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
                success = self.download_service.download_env_file(py_file_name, py_file_path, progress_callback=progress_callback)
                if not success:  # 下载失败的 直接返回失败 不重试
                    return False

            if progress_callback is not None:
                progress_callback(-1, '正在安装pip')
            # deprecated: 直接使用配置的pip源
            # self.choose_best_pip_source(progress_callback)
            result = cmd_utils.run_command([python_path, py_file_path, '--index-url', self.env_config.pip_source])
            success = result is not None
            msg = '安装pip成功' if success else '安装pip失败 准备重试'
            log.info(msg)
            if progress_callback is not None:
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
        if progress_callback is not None:
            progress_callback(-1, '正在安装virtualenv')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'pip', 'install', 'virtualenv', '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = '安装virtualenv成功' if success else '安装virtualenv失败'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(1 if success else 0, msg)
        return success

    def create_default_venv(self, progress_callback: Optional[Callable[[float, str], None]]) -> bool:
        """
        创建默认的虚拟环境
        :param progress_callback:
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '准备创建虚拟环境')
        python_path = self.env_config.python_path
        result = cmd_utils.run_command([python_path, '-m', 'virtualenv', DEFAULT_VENV_DIR_PATH, '--always-copy'])
        success = result is not None
        msg = '创建虚拟环境成功' if success else '创建虚拟环境失败'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(1 if success else 0, msg)
        return success

    def uv_create_venv(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> bool:
        """
        使用uv创建虚拟环境
        :param progress_callback:
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '开始使用 UV 创建虚拟环境')
        log.info('开始使用 UV 创建虚拟环境')
        os.environ["UV_PYTHON_INSTALL_DIR"] = DEFAULT_PYTHON_DIR_PATH
        result = cmd_utils.run_command([self.env_config.uv_path, 'venv', DEFAULT_VENV_DIR_PATH, '--python=3.11.12', '--no-python-downloads'])
        success = result is not None
        msg = '创建虚拟环境成功' if success else '创建虚拟环境失败'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(1 if success else 0, msg)
            return True

    def uv_sync(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        使用 UV 安装环境和依赖
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '正在安装...')
        log.info('开始使用 UV 安装依赖')
        os.environ["UV_PYTHON_INSTALL_DIR"] = DEFAULT_PYTHON_DIR_PATH
        result = cmd_utils.run_command([self.env_config.uv_path, 'sync'])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        log.info(msg)
        return success, msg

    def get_os_uv_path(self) -> Optional[str]:
        """
        获取当前系统环境变量中的uv路径
        :return:
        """
        log.info('获取系统环境变量中的 UV')
        message = cmd_utils.run_command(['where', 'uv'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_os_python_path(self) -> Optional[str]:
        """
        获取当前系统环境变量中的python路径
        :return:
        """
        log.info('获取系统环境变量中的 Python')
        message = cmd_utils.run_command(['where', 'python'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_uv_version(self) -> Optional[str]:
        """
        :return: 当前使用的uv版本
        """
        log.info('检测当前 UV 版本')
        uv_path = self.env_config.uv_path
        if uv_path == '' or not os.path.exists(uv_path):
            return None

        version = cmd_utils.run_command([uv_path, '--version'])
        if version is not None:
            return version[3:]
        else:
            return None

    def get_python_version(self) -> Optional[str]:
        """
        :return: 当前使用的python版本
        """
        log.info('检测当前 Python 版本')
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
            return False, '安装Python失败 请尝试到「设置」更改网络代理'
        self.env_config.python_path = DEFAULT_PYTHON_PATH
        if not self.install_default_pip(progress_callback):
            return False, '安装pip失败 请尝试到「设置」更改网络代理'
        if not self.install_default_virtualenv(progress_callback):
            return False, '安装virtualenv失败'
        if not self.create_default_venv(progress_callback):
            return False, '创建虚拟环境失败'
        self.env_config.python_path = DEFAULT_VENV_PYTHON_PATH

        return True, ''

    def uv_install_python_venv(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> Tuple[bool, str, str]:
        """
        完整流程使用 uv 安装 python 环境
        :param progress_callback:
        :return:
        """
        # 清理旧环境
        if progress_callback is not None:
            progress_callback(-1, '正在清理旧文件')
        self.env_config.python_path = ''
        if os.path.exists(DEFAULT_PYTHON_DIR_PATH):
            shutil.rmtree(DEFAULT_PYTHON_DIR_PATH)

        if os.path.exists(DEFAULT_VENV_DIR_PATH):
            shutil.rmtree(DEFAULT_VENV_DIR_PATH)

        if not self.uv_install_python(progress_callback):
            return False, '安装 Python 失败 请尝试到「设置」更改 Python 下载源'

        if not self.uv_sync(progress_callback):
            return False, '创建环境失败'
        self.env_config.python_path = DEFAULT_VENV_PYTHON_PATH

        return True, ''

    def install_requirements(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        安装依赖
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '正在安装...安装过程需要5~10分钟，请耐心等待')

        # 部分人不升级pip会安装失败 不知道为什么
        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade', 'pip',
                                        '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        if not success:
            return success, msg

        result = cmd_utils.run_command([self.env_config.python_path, '-m', 'pip', 'install', '--upgrade',
                                        '-r', os.path.join(os_utils.get_work_dir(), self.project_config.requirements),
                                        '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        return success, msg

    def uv_install_requirements(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        使用 UV 安装依赖
        :return:
        """
        if progress_callback is not None:
            progress_callback(-1, '正在安装...')

        # result = cmd_utils.run_command([self.env_config.uv_path, 'pip', 'install', '--upgrade', '--link-mode=copy',
        #                                 '-r', os.path.join(os_utils.get_work_dir(), self.project_config.requirements),
        #                                 '--index-url', self.env_config.pip_source, '--trusted-host', self.env_config.pip_trusted_host])
        result = cmd_utils.run_command([self.env_config.uv_path, 'sync'])
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

    def _choose_best_source_by_ping(
        self,
        source_enum_cls,
        log_prefix: str,
        config_attr_name: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Optional[Tuple[str, int]]:
        """
        对指定类型的源进行测速 并选择最佳一个
        :param source_enum_cls: 源的枚举类 (例如 PipSourceEnum, CpythonSourceEnum)
        :param log_prefix: 日志前缀 (例如 "pip源", "Python下载源")
        :param config_attr_name: self.env_config 中要更新的属性名 (例如 "pip_source", "cpython_source")
        :param progress_callback: 进度回调
        :return: (最佳源的标签, 延迟ms) or None if no sources or all fail
        """
        display_log = f'开始{log_prefix}测速'
        log.info(display_log)
        if progress_callback is not None:
            progress_callback(-1, display_log)

        ping_result_list = []
        sources_to_test = list(source_enum_cls)
        if not sources_to_test:
            log.warning(f"没有找到{log_prefix}以进行测速")
            if progress_callback is not None:
                progress_callback(-1, f"没有找到{log_prefix}以进行测速")
            return None

        for source_enum_member in sources_to_test:
            source = source_enum_member.value
            source_url = source.value
            parsed_url = urllib.parse.urlparse(source_url)
            domain = parsed_url.netloc
            start_time = time.time()
            result = cmd_utils.run_command(['ping', '-n', '1', '-w', '1000', domain])
            end_time = time.time()

            ms_match = None
            if result is not None:
                ms_match = re.search(r'(\d+)ms', result)

            if ms_match:
                ms = int(ms_match.group(1))
            else:
                elapsed_ms = int(1000 * (end_time - start_time))
                ms = elapsed_ms if elapsed_ms < 3000 else 9999

            current_source_log = f'{source.label} 耗时 {ms}ms'
            log.info(current_source_log)
            if progress_callback is not None:
                progress_callback(-1, current_source_log)

            ping_result_list.append((source, ms))

        if not ping_result_list:
            log.warning(f"所有{log_prefix}测速失败")
            if progress_callback is not None:
                progress_callback(-1, f"所有{log_prefix}测速失败")
            return None

        ping_result_list.sort(key=lambda x: x[1])

        best_source_obj = ping_result_list[0][0]
        best_source_ms = ping_result_list[0][1]

        final_log_msg = f'选择最优{log_prefix} {best_source_obj.label}'
        log.info(final_log_msg)
        if progress_callback is not None:
            progress_callback(-1, final_log_msg)

        setattr(self.env_config, config_attr_name, best_source_obj.value)
        return best_source_obj.label, best_source_ms

    def choose_best_pip_source(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[Tuple[str, int]]:
        """
        对pip源进行测速 并选择最佳一个
        :return: (最佳源的标签, 延迟ms) or None if no sources
        """
        return self._choose_best_source_by_ping(
            PipSourceEnum,
            "pip源",
            "pip_source",
            progress_callback
        )

    def choose_best_cpython_source(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[Tuple[str, int]]:
        """
        对Python下载源进行测速 并选择最佳一个
        :return: (最佳源的标签, 延迟ms) or None if no sources
        """
        return self._choose_best_source_by_ping(
            CpythonSourceEnum,
            "Python下载源",
            "cpython_source",
            progress_callback
        )


if __name__ == '__main__':
    project_config = ProjectConfig()
    env_config = EnvConfig()
    download_service = DownloadService(project_config, env_config)
    python_service = PythonService(project_config, env_config, download_service)
    python_service.uv_install_requirements(None)
