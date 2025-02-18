from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor
from typing import Tuple

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class VenvInstallCard(BaseInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='运行依赖',
            install_method=ctx.python_service.install_requirements
        )

    def after_progress_done(self, success: bool, msg: str) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success: 是否成功
        :param msg: 提示信息
        :return:
        """
        if success:
            self.ctx.env_config.requirement_time = self.ctx.git_service.get_requirement_time()
            self.check_and_update_display()
        else:
            self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value), gt(msg, 'ui'))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        last = self.ctx.env_config.requirement_time

        if last != self.ctx.git_service.get_requirement_time():
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
            msg = gt('需更新，请使用安装器更新', 'ui')
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已安装', 'ui')}" + ' ' + last

        return icon, msg
