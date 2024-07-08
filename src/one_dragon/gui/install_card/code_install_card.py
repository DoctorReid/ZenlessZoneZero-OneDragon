from typing import Tuple

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor

from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.gui.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class CodeInstallCard(BaseInstallCard):

    def __init__(self, ctx: OneDragonContext, parent=None):

        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='代码版本',
            install_method=ctx.git_service.fetch_latest_code,
            install_btn_icon=FluentIcon.SYNC,
            install_btn_text_cn='代码同步',
            parent=parent
        )

    def after_progress_done(self, success: bool) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success:
        :return:
        """
        if success:
            self.check_and_update_display()
        else:
            self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value), gt('同步失败', 'ui'))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        current_branch = self.ctx.git_service.get_current_branch()
        if current_branch is None:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未同步代码', 'ui')
        elif current_branch != self.ctx.project_config.project_git_branch:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
            msg = f"{gt('当前分支', 'ui')}: {current_branch}; {gt('建议分支', 'ui')}: {self.ctx.project_config.project_git_branch}; {gt('不自动同步', 'ui')}"
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已同步代码', 'ui')}" + ' ' + current_branch

        return icon, msg
