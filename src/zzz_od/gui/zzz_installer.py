import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from qfluentwidgets import Theme, setTheme


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # QMessageBox.information(None, '提示', '请选择安装路径')
    work_dir = QFileDialog.getExistingDirectory(None, '请选择安装路径')
    if not work_dir:
        sys.exit(0)
    os.chdir(work_dir)

    # 延迟导入
    from zzz_od.gui.zzz_installer_window import ZInstallerWindow
    from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
    from one_dragon.utils.i18_utils import gt

    ZInstallerWindow._unpack_resources()
    _ctx = OneDragonEnvContext()
    _ctx.async_update_gh_proxy()
    setTheme(Theme['AUTO'])
    w = ZInstallerWindow(_ctx, gt(f'{_ctx.project_config.project_name}-installer', 'ui'))
    w.show()
    app.exec()
    _ctx.after_app_shutdown()
