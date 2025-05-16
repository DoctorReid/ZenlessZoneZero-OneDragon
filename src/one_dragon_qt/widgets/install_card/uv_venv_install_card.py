from one_dragon_qt.widgets.install_card.venv_install_card import VenvInstallCard

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard


class UVVenvInstallCard(VenvInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='手动安装依赖 (UV)',
            install_method=ctx.python_service.uv_install_requirements,
        )