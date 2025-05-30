from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor
from typing import Tuple

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class LauncherInstallCard(BaseInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='安装启动器',
            install_method=ctx.python_service.install_launcher
        )

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
        if self.ctx.python_service.check_launcher_exist():
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已安装', 'ui')}"
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('需下载', 'ui')
        return icon, msg