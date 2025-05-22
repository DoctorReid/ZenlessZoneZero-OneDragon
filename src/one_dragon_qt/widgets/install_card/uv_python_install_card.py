from one_dragon_qt.widgets.install_card.python_install_card import PythonInstallCard

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard

class UVPythonInstallCard(PythonInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        WithExistedInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='Python虚拟环境 (UV)',
            install_method=ctx.python_service.uv_install_python_venv,
        )