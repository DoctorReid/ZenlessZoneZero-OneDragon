from typing import Tuple

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor

from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.gui.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class VenvInstallCard(BaseInstallCard):

    def __init__(self, ctx: OneDragonContext):
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='运行依赖',
            install_method=ctx.python_service.install_requirements
        )

    def after_progress_done(self, success: bool) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success:
        :return:
        """
        if success:
            self.ctx.env_config.requirement_time = self.ctx.git_service.get_requirement_time()
            self.check_and_update_display()
        else:
            self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value), gt('安装失败', 'ui'))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        last = self.ctx.env_config.requirement_time

        if last == '':
            icon =FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装', 'ui')
        elif last != self.ctx.git_service.get_requirement_time():
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
            msg = gt('需更新', 'ui')
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已安装', 'ui')}" + ' ' + last

        return icon, msg
