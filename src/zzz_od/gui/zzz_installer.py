import os, sys, shutil

from qfluentwidgets import NavigationItemPosition

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.app.installer import InstallerWindowBase
from one_dragon_qt.view.code_interface import CodeInterface
from one_dragon_qt.view.installer_interface import InstallerInterface
from one_dragon_qt.view.uv_installer_interface import UVInstallerInterface
from one_dragon_qt.view.installer_setting_interface import InstallerSettingInterface
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

    def create_sub_interface(self):
        # self.add_sub_interface(InstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(UVInstallerInterface(self.ctx, parent=self))
        self.add_sub_interface(ExtendInstallInterface(self.ctx, parent=self))
        self.add_sub_interface(CodeInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)
        self.add_sub_interface(InstallerSettingInterface(self.ctx, parent=self), position=NavigationItemPosition.BOTTOM)

    def _unpack_resources():
        if hasattr(sys, '_MEIPASS'):
            work_dir = os.getcwd()
            resources_path = os.path.join(sys._MEIPASS, 'resources')
            if os.path.exists(resources_path):
                for root, dirs, files in os.walk(resources_path):
                    rel_path = os.path.relpath(root, resources_path)
                    dest_dir = os.path.join(work_dir, rel_path) if rel_path != '.' else work_dir
                    os.makedirs(dest_dir, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        shutil.move(src_file, dest_file)
