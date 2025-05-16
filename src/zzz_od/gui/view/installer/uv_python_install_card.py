from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
import subprocess
import os
from one_dragon.utils.i18_utils import gt
from PySide6.QtGui import QIcon
import shutil
from one_dragon.utils import os_utils

class UvPythonInstallCard(WithExistedInstallCard):
    def __init__(self, ctx):
        super().__init__(
            ctx=ctx,
            title_cn='Python虚拟环境',
            install_method=self.uv_install_python_venv,
            install_btn_icon=FluentIcon.DOWN,
            install_btn_text_cn='默认安装',
            content_cn='未安装'
        )
        self.ctx = ctx

    def uv_install_python_venv(self, progress_callback):
        # 检查uv是否已安装
        uv_path = shutil.which('uv')
        if not uv_path:
            return False, gt('未检测到uv，请先手动安装uv', 'ui')
        if progress_callback:
            progress_callback(-1, gt('正在用uv创建虚拟环境...', 'ui'))
        # 用和原有逻辑一致的.env/venv目录
        venv_dir = os_utils.get_path_under_work_dir('.env', 'venv')
        try:
            result = subprocess.run([
                'uv', 'venv', venv_dir, '--python=3.11.9'
            ], timeout=120)
            if result.returncode != 0:
                return False, gt('uv创建虚拟环境失败', 'ui')
        except Exception as e:
            return False, gt('uv创建虚拟环境异常', 'ui') + str(e)
        python_path = os.path.join(venv_dir, 'Scripts', 'pythonw.exe')
        if not os.path.exists(python_path):
            return False, gt('未找到虚拟环境pythonw.exe', 'ui')
        self.ctx.env_config.python_path = python_path
        if progress_callback:
            progress_callback(1, gt('uv虚拟环境创建成功', 'ui'))
        return True, gt('uv虚拟环境创建成功', 'ui')

    def get_display_content(self):
        # 检查uv是否存在
        uv_path = shutil.which('uv')
        if not uv_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装uv', 'ui')
            return icon, msg
        python_path = self.ctx.env_config.python_path
        if not python_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装。可选择你自己的虚拟环境的python.exe，或默认安装。', 'ui')
            return icon, msg
        elif not os.path.exists(python_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('文件不存在', 'ui') + ' ' + python_path
            return icon, msg
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = gt('已安装', 'ui') + ' ' + python_path
            return icon, msg 