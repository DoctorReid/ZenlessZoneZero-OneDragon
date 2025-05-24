import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # QMessageBox.information(None, '提示', '请选择安装路径')
    work_dir = QFileDialog.getExistingDirectory(None, '请选择安装路径')
    if not work_dir:
        sys.exit(0)
    os.chdir(work_dir)
    from zzz_od.gui.zzz_installer import ZInstallerWindow
    ZInstallerWindow._unpack_resources(work_dir)
    from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
    from qfluentwidgets import Theme, setTheme
    from one_dragon.utils.i18_utils import gt
    _ctx = OneDragonEnvContext()
    _ctx.async_update_gh_proxy()
    setTheme(Theme['AUTO'])
    w = ZInstallerWindow(_ctx, gt(f'{_ctx.project_config.project_name}-installer', 'ui'))
    w.show()
    app.exec()
    _ctx.after_app_shutdown()
