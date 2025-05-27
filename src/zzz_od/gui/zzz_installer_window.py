import os, sys, shutil

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.app.installer import InstallerWindowBase
from one_dragon_qt.view.uv_installer_interface import UVInstallerInterface
from one_dragon_qt.view.installer_setting_interface import InstallerSettingInterface
from zzz_od.gui.view.installer.uv_gamepad_install_card import UVGamepadInstallCard


class ZInstallerWindow(InstallerWindowBase):


    def __init__(self, ctx: OneDragonEnvContext, win_title: str, parent=None):
        InstallerWindowBase.__init__(
            self,
            ctx=ctx,
            win_title=win_title,
            parent=parent,
            app_icon='zzz_logo.ico'
        )

        # 隐藏左侧导航栏
        self.navigationInterface.setVisible(False)

        # 调整标题栏位置使其左对齐
        self._adjust_title_bar_position()

    def _adjust_title_bar_position(self):
        """调整标题栏位置到左边"""
        self.titleBar.move(0, 0)
        self.titleBar.resize(self.width(), self.titleBar.height())

    def resizeEvent(self, event):
        """重写窗口大小改变事件"""
        super().resizeEvent(event)
        self._adjust_title_bar_position()

    def create_sub_interface(self):
        extend_install_cards = [UVGamepadInstallCard(self.ctx)]
        self.add_sub_interface(UVInstallerInterface(self.ctx, parent=self, 
                                                    extra_install_cards=extend_install_cards),)

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
