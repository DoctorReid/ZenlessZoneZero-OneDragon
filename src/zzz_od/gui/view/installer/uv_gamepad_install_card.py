from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from zzz_od.gui.view.installer.gamepad_install_card import GamepadInstallCard


class UVGamepadInstallCard(GamepadInstallCard):

    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        self.ctx: OneDragonEnvContext = ctx
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='虚拟手柄 (UV)',
            install_method=self.uv_install_requirements,
            parent=parent
        )
