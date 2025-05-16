from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
from one_dragon.utils import cmd_utils
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
        # 安装python到本地
        cpython_build_source = getattr(self.ctx.env_config, 'cpython_build_source', None)
        try:
            install_cmd = ['uv', 'python', 'install', '3.11.12']
            if cpython_build_source:
                install_cmd += ['--mirror', cpython_build_source]
            result = cmd_utils.run_command(install_cmd)
            if result is None:
                return False, gt('uv安装python失败', 'ui')
        except Exception as e:
            return False, gt('uv安装python异常', 'ui') + str(e)
        # 创建虚拟环境
        venv_dir = os_utils.get_path_under_work_dir('.env', 'venv')
        try:
            result = cmd_utils.run_command(['uv', 'venv', venv_dir, '--python=3.11.12'])
            if result is None:
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
            msg = gt('未安装uv，点击安装按钮将自动安装', 'ui')
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

    def on_existed_chosen(self, file_path: str) -> None:
        """
        选择了本地文件之后的回调
        :param file_path: 本地文件的路径
        :return:
        """
        self.ctx.env_config.python_path = file_path  # 这会通过 setter 自动保存配置
        self.check_and_update_display()  # 更新卡片显示内容
        self.finished.emit(True)  # 发射完成信号 