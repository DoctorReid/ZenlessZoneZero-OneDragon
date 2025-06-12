import os
from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor
from typing import Tuple

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from one_dragon.utils.i18_utils import gt


class PythonInstallCard(WithExistedInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        WithExistedInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='Python 虚拟环境',
            install_method=ctx.python_service.uv_install_python_venv,
        )

    def on_existed_chosen(self, file_path: str) -> None:
        """
        选择了本地文件之后的回调，由子类自行实现
        :param file_path: 本地文件的路径
        :return:
        """
        self.ctx.env_config.python_path = file_path
        self.check_and_update_display()

    def after_progress_done(self, success: bool, msg: str) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success: 是否成功
        :param msg: 提示信息
        :return:
        """
        if success:
            self.check_and_update_display()
        else:
            self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value), gt(msg, 'ui'))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        python_path = self.ctx.env_config.python_path

        if python_path == '':
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装。可选择 .venv 文件夹中的 python.exe', 'ui')
        elif not os.path.exists(python_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('文件不存在', 'ui') + ' ' + python_path
        elif ".venv" not in python_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('仅支持 .venv 作为 Python 虚拟环境文件夹命名', 'ui') + ' ' + python_path
        else:
            python_version = self.ctx.python_service.get_python_version()
            if python_version is None:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
                msg = gt('无法获取 Python 版本', 'ui') + ' ' + python_path
            elif self.ctx.project_config.python_version not in python_version:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
                msg = (f"{gt('当前版本', 'ui')}: {python_version}; {gt('建议版本', 'ui')}: {self.ctx.project_config.python_version}"
                       + ' ' + python_path)
            else:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
                msg = f"{gt('已安装', 'ui')}" + ' ' + python_path

        return icon, msg
