import os, sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import NavigationItemPosition, Theme, setTheme

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.app.installer import InstallerWindowBase
from one_dragon_qt.view.code_interface import CodeInterface
from one_dragon_qt.view.installer_interface import InstallerInterface
from one_dragon_qt.view.uv_installer_interface import UVInstallerInterface
from one_dragon_qt.view.installer_setting_interface import InstallerSettingInterface
from one_dragon_qt.widgets.welcome_dialog import WelcomeDialog
from one_dragon.utils.i18_utils import gt
from zzz_od.gui.view.installer.extend_install_interface import ExtendInstallInterface


class ZInstallerWindow(InstallerWindowBase):

    def __init__(self, ctx: OneDragonEnvContext, win_title: str, parent=None):
        InstallerWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=win_title,
            parent=parent,
            app_icon='zzz_logo.ico'
        )
        self._check_first_run()

    def create_sub_interface(self):
        # self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(UVInstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(ExtendInstallInterface(self.ctx, parent=self))
        self.add_sub_interface(CodeInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)

    def _check_first_run(self):
        """首次运行时显示防倒卖弹窗"""
        if self.ctx.env_config.is_first_run:
            dialog = WelcomeDialog(self)
            if dialog.exec():
                self.ctx.env_config.is_first_run = False

def _unpack_resources():
    if hasattr(sys, '_MEIPASS'):
        path = os.path.dirname(sys.argv[0])
        os.chdir(path)
        resources_path = os.path.join(sys._MEIPASS, 'resources')
        if os.path.exists(resources_path):
            import shutil
            for root, dirs, files in os.walk(resources_path):
                rel_path = os.path.relpath(root, resources_path)
                dest_dir = os.path.join(path, rel_path) if rel_path != '.' else path
                os.makedirs(dest_dir, exist_ok=True)
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.move(src_file, dest_file)


if __name__ == '__main__':
    _unpack_resources()
    app = QApplication(sys.argv)
    _ctx = OneDragonEnvContext()
    # 异步更新免费代理
    _ctx.async_update_gh_proxy()
    setTheme(Theme['AUTO'])
    w = ZInstallerWindow(_ctx, gt(f'{_ctx.project_config.project_name}-installer', 'ui'))
    w.show()
    app.exec()

    _ctx.after_app_shutdown()
