from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
from one_dragon.utils import cmd_utils
import shutil
import os
from one_dragon.utils.i18_utils import gt

class UvUvInstallCard(WithExistedInstallCard):
    def __init__(self, ctx):
        super().__init__(
            ctx=ctx,
            title_cn='UV',
            install_method=self.uv_install_uv,
            install_btn_icon=FluentIcon.DOWN,
            install_btn_text_cn='默认安装',
            content_cn='未安装'
        )
        self.ctx = ctx

    def uv_install_uv(self, progress_callback):
        uv_path = getattr(self.ctx.env_config, 'uv_path', None)
        if uv_path and os.path.exists(uv_path):
            if progress_callback:
                progress_callback(1, gt('已检测到uv，无需重复安装', 'ui'))
            return True, gt('已检测到uv，无需重复安装', 'ui')
        if progress_callback:
            progress_callback(-1, gt('正在安装UV...', 'ui'))
        try:
            result = cmd_utils.run_command([
                'powershell',
                '-ExecutionPolicy',
                'ByPass',
                '-c',
                'irm https://astral.sh/uv/install.ps1 | iex'
            ])
            if result is None:
                return False, gt('UV安装失败', 'ui')
        except Exception as e:
            return False, gt('UV安装异常', 'ui') + str(e)
        uv_path = shutil.which('uv')
        if uv_path and os.path.exists(uv_path):
            self.ctx.env_config.uv_path = uv_path
            if progress_callback:
                progress_callback(1, gt('UV安装成功', 'ui'))
            return True, gt('UV安装成功', 'ui')
        else:
            return False, gt('UV安装后未检测到uv.exe', 'ui')

    def get_display_content(self):
        uv_path = shutil.which('uv')
        if not uv_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装UV，点击安装按钮将自动安装', 'ui')
            return icon, msg
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = gt('已安装UV', 'ui') + ' ' + uv_path
            return icon, msg