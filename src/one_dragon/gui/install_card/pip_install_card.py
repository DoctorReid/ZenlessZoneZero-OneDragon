import os
from typing import Optional, Tuple

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor

from one_dragon.envs.env_config import EnvConfig, env_config, DEFAULT_PIP_PATH
from one_dragon.envs.project_config import ProjectConfig, project_config
from one_dragon.envs.python_service import python_service, PythonService
from one_dragon.gui.install_card.wtih_existed_install_card import WithExistedInstallCard
from one_dragon.utils.i18_utils import gt


class PipInstallCard(WithExistedInstallCard):

    def __init__(self):
        self.env_config: EnvConfig = env_config
        self.project_config: ProjectConfig = project_config
        self.python_service: PythonService = python_service

        super().__init__(
            title_cn='Pip',
            install_method=self.python_service.install_default_pip,
        )

    def get_existed_os_path(self) -> Optional[str]:
        """
        获取系统环境变量中的路径，由子类自行实现
        :return:
        """
        return self.python_service.get_os_pip_path()

    def on_existed_chosen(self, file_path: str) -> None:
        """
        选择了本地文件之后的回调，由子类自行实现
        :param file_path: 本地文件的路径
        :return:
        """
        self.env_config.pip_path = file_path
        self.check_and_update_display()

    def after_progress_done(self, success: bool) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success:
        :return:
        """
        if success:
            self.env_config.pip_path = DEFAULT_PIP_PATH
            self.check_and_update_display()
        else:
            self.setContent(gt('安装失败', 'ui'))
            self.iconLabel.setIcon(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        pip_path = self.env_config.pip_path

        if pip_path == '':
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装', 'ui')
        elif not os.path.exists(pip_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('文件不存在', 'ui') + ' ' + pip_path
        else:
            pip_version = self.python_service.get_pip_version()
            if pip_version is None:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
                msg = gt('无法获取Pip版本', 'ui') + ' ' + pip_path
            elif pip_version != self.project_config.pip_version:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
                msg = (f"{gt('当前版本', 'ui')}: {pip_version}; {gt('建议版本', 'ui')}: {self.project_config.pip_version}"
                       + ' ' + pip_path)
            else:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
                msg = f"{gt('已安装', 'ui')}" + ' ' + pip_path

        return icon, msg
