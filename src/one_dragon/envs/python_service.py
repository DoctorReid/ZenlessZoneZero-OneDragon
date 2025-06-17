import os.path
import time

import re
import shutil
import urllib.parse
from typing import Optional, Callable, Tuple

from one_dragon.envs.env_config import EnvConfig, PipSourceEnum, CpythonSourceEnum, DEFAULT_ENV_PATH, DEFAULT_UV_DIR_PATH,\
     DEFAULT_PYTHON_DIR_PATH, DEFAULT_VENV_DIR_PATH, DEFAULT_VENV_PYTHON_PATH
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

        msg = '正在安装 UV...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        for _ in range(2):
            zip_file_name = 'uv-x86_64-pc-windows-msvc.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.download_service.download_env_file(zip_file_name, zip_file_path, progress_callback=progress_callback)
                if not success:
                    return False, '下载 UV 失败 请尝试到「设置」更改网络代理'

            msg = f'正在解压 {zip_file_name}...'
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
        return False, '安装 UV 失败'

    def uv_install_python(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> bool:
        """
        使用uv安装python
        """
        if not self.env_config.uv_path:
            if progress_callback is not None:
                progress_callback(0, '未找到 UV 路径')
            return False

        msg = '正在使用 UV 安装 Python...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        source = self.env_config.cpython_source
        if source == CpythonSourceEnum.GITHUB.value.value and self.env_config.is_gh_proxy:
            source = f'{self.env_config.gh_proxy_url}/{source}'
        result = cmd_utils.run_command([self.env_config.uv_path, 'python', 'install', self.project_config.python_version,
                                        '--mirror', source,
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

    def uv_create_venv(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> bool:
        """
        使用uv创建虚拟环境
        :param progress_callback:
        :return:
        """
        msg = '正在使用 UV 创建虚拟环境...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

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
        使用uv安装环境和依赖
        :return:
        """
        msg = '正在使用 UV 安装依赖...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        os.environ["UV_PYTHON_INSTALL_DIR"] = DEFAULT_PYTHON_DIR_PATH
        result = cmd_utils.run_command([self.env_config.uv_path, 'sync', '--default-index', self.env_config.pip_source,])
        success = result is not None
        msg = '运行依赖安装成功' if success else '运行依赖安装失败'
        log.info(msg)
        return success, msg

    def uv_check_sync_status(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        检查环境是否与项目同步
        :param progress_callback: 进度回调
        :return: (是否同步, 状态信息)
        """
        msg = '正在检查环境同步状态...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        os.environ["UV_PYTHON_INSTALL_DIR"] = DEFAULT_PYTHON_DIR_PATH
        result = cmd_utils.run_command([self.env_config.uv_path, 'sync', '--check'])

        is_synced = result is not None
        msg = '环境已同步' if is_synced else '环境未同步'
        log.info(msg)

        return is_synced, msg

    def get_os_uv_path(self) -> Optional[str]:
        """
        获取当前系统环境变量中的uv路径
        :return:
        """
        log.debug('获取系统环境变量中的 UV')
        message = cmd_utils.run_command(['where', 'uv'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_uv_version(self) -> Optional[str]:
        """
        :return: 当前使用的uv版本
        """
        log.debug('检测当前 UV 版本')
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
        log.debug('检测当前 Python 版本')
        python_path = self.env_config.python_path
        if python_path == '' or not os.path.exists(python_path):
            return None

        version = cmd_utils.run_command([python_path, '--version'])  # Ex: Python 3.11.9
        if version is not None:
            return version[7:]
        else:
            return None

    def uv_install_python_venv(self, progress_callback: Optional[Callable[[float, str, str], None]]) -> Tuple[bool, str]:
        """
        完整流程使用uv安装python环境
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

        if not self.uv_create_venv(progress_callback):
            return False, '创建环境失败'
        self.env_config.python_path = DEFAULT_VENV_PYTHON_PATH

        return True, ''

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
        msg = f'正在进行{log_prefix}测速...'
        if progress_callback is not None:
            progress_callback(-1, msg)
        log.info(msg)

        ping_result_list = []
        sources_to_test = list(source_enum_cls)
        if not sources_to_test:
            log.warning(f"找不到{log_prefix}以进行测速")
            if progress_callback is not None:
                progress_callback(-1, f"找不到{log_prefix}以进行测速")
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
    python_service.uv_check_sync_status()
