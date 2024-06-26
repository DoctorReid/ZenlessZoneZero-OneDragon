import os
from enum import Enum
from typing import Optional

from one_dragon.base.yaml_config import YamlConfig
from one_dragon.utils import os_utils


DEFAULT_ENV_PATH = os_utils.get_path_under_work_dir('.env')
DEFAULT_GIT_DIR_PATH = os.path.join(DEFAULT_ENV_PATH, 'PortableGit')  # 默认的git文件夹路径
DEFAULT_GIT_PATH = os.path.join(DEFAULT_GIT_DIR_PATH, 'cmd', 'git.exe')  # 默认的git.exe文件路径
DEFAULT_PYTHON_DIR_PATH = os_utils.get_path_under_work_dir('.env', 'python')  # 默认的python文件夹路径 这个赋值会创建空文件夹
DEFAULT_PYTHON_PATH = os.path.join(DEFAULT_PYTHON_DIR_PATH, 'python.exe')  # 默认安装的python路径
DEFAULT_PYTHON_PTH_PATH = os.path.join(DEFAULT_PYTHON_DIR_PATH, 'python311._pth')  # 默认安装的python配置文件路径
DEFAULT_PYTHON_SCRIPTS_DIR_PATH = os_utils.get_path_under_work_dir('.env', 'python', 'Scripts')  # 默认的python环境中的其它exe文件夹路径
DEFAULT_PIP_PATH = os.path.join(DEFAULT_PYTHON_SCRIPTS_DIR_PATH, 'pip.exe')  # 默认安装的pip路径

GH_PROXY_URL = 'https://mirror.ghproxy.com/'  # 免费代理的路径


class ProxyType(Enum):

    NONE: str = '无'
    PERSONAL: str = '个人代理',
    GHPROXY: str = '免费代理'


class EnvConfig(YamlConfig):

    def __init__(self):
        super().__init__(module_name='env')

    @property
    def git_path(self) -> str:
        """
        :return: git的路径
        """
        return self.get('git_path', '')

    @git_path.setter
    def git_path(self, new_value: str) -> None:
        """
        更新 git的路径 正常不需要调用
        :param new_value:
        :return:
        """
        self.update('git_path', new_value)

    @property
    def python_path(self) -> str:
        """
        :return: python的路径
        """
        return self.get('python_path', '')

    @python_path.setter
    def python_path(self, new_value: str) -> None:
        """
        更新 python的路径 正常不需要调用
        :param new_value:
        :return:
        """
        self.update('python_path', new_value)

    @property
    def pip_path(self) -> str:
        """
        :return: pip的路径
        """
        return self.get('pip_path', '')

    @pip_path.setter
    def pip_path(self, new_value: str) -> None:
        """
        更新 pip的路径 正常不需要调用
        :param new_value: pip路径
        :return:
        """
        self.update('pip_path', new_value)

    @property
    def proxy_type(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('proxy_type', ProxyType.GHPROXY.value)

    @proxy_type.setter
    def proxy_type(self, new_value: str) -> None:
        """
        更新代理类型
        :return:
        """
        self.update('proxy_type', new_value)

    @property
    def personal_proxy(self) -> str:
        """
        代理类型
        :return:
        """
        return self.get('personal_proxy', '')

    @personal_proxy.setter
    def personal_proxy(self, new_value: str) -> None:
        """
        更新代理类型
        :return:
        """
        self.update('personal_proxy', new_value)

    @property
    def proxy_address(self) -> Optional[str]:
        """
        :return: 真正使用的代理地址
        """
        proxy_type = self.proxy_type
        if proxy_type == ProxyType.NONE.value:
            return None
        elif proxy_type == ProxyType.GHPROXY.value:
            return GH_PROXY_URL
        elif proxy_type == ProxyType.PERSONAL.value:
            proxy = self.personal_proxy
            return None if proxy == '' else proxy
        return None

    @property
    def requirement_time(self) -> str:
        """
        安装依赖时 使用的 requirement.txt 的最后修改时间
        :return:
        """
        return self.get('requirement_time', '')

    @requirement_time.setter
    def requirement_time(self, new_value: str) -> None:
        """
        安装依赖时 使用的 requirement.txt 的最后修改时间
        :return:
        """
        self.update('requirement_time', new_value)

    @property
    def repository_from(self) -> str:
        """
        代码托管地方
        :return:
        """
        return self.get('repository_from', 'github')

    @repository_from.setter
    def repository_from(self, new_value: str) -> None:
        """
        代码托管地方
        :return:
        """
        self.update('repository_from', new_value)

    @property
    def git_method(self) -> str:
        """
        git使用https还是ssh
        :return:
        """
        return self.get('git_method', 'https')

    @git_method.setter
    def git_method(self, new_value: str) -> None:
        """
        git使用https还是ssh
        :return:
        """
        self.update('git_method', new_value)

    @property
    def pip_source(self) -> str:
        """
        pip源
        :return:
        """
        return self.get('pip_source', 'https://pypi.tuna.tsinghua.edu.cn/simple')

    @pip_source.setter
    def pip_source(self, new_value: str) -> None:
        """
        pip源
        :return:
        """
        self.update('pip_source', new_value)


env_config = EnvConfig()
