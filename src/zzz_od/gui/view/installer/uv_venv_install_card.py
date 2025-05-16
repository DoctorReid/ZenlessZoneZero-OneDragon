from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
import subprocess
import os
from one_dragon.utils.i18_utils import gt
from PySide6.QtGui import QIcon

class UvVenvInstallCard(BaseInstallCard):
    def __init__(self, ctx):
        super().__init__(
            ctx=ctx,
            title_cn='运行依赖',
            install_method=self.uv_install_requirements,
            install_btn_icon=FluentIcon.DOWN,
            install_btn_text_cn='默认安装',
            content_cn='未安装'
        )
        self.ctx = ctx

    def uv_install_requirements(self, progress_callback):
        if progress_callback:
            progress_callback(-1, gt('正在用uv安装依赖...', 'ui'))
        python_path = self.ctx.env_config.python_path
        if not python_path or not os.path.exists(python_path):
            return False, gt('未检测到虚拟环境python.exe', 'ui')
        venv_dir = os.path.dirname(os.path.dirname(python_path))
        requirements = self.ctx.project_config.requirements
        req_path = os.path.join(os.getcwd(), requirements)
        try:
            result = subprocess.run([
                'uv', 'pip', 'install', '-r', req_path
            ], cwd=venv_dir, timeout=300)
            if result.returncode != 0:
                return False, gt('uv安装依赖失败', 'ui')
        except Exception as e:
            return False, gt('uv安装依赖异常', 'ui') + str(e)
        if progress_callback:
            progress_callback(1, gt('uv依赖安装成功', 'ui'))
        return True, gt('uv依赖安装成功', 'ui')

    def get_display_content(self):
        python_path = self.ctx.env_config.python_path
        if not python_path or not os.path.exists(python_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未检测到虚拟环境python.exe', 'ui')
            return icon, msg
        last = self.ctx.env_config.requirement_time
        current = self.ctx.git_service.get_requirement_time()
        if last != current:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
            msg = gt('需更新，请使用安装器更新', 'ui')
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已安装', 'ui')} {last}"
        return icon, msg 