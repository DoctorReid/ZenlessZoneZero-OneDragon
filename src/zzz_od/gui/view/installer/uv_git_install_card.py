from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
import subprocess
import shutil
import os
from one_dragon.utils.i18_utils import gt
from one_dragon.envs.env_config import DEFAULT_GIT_PATH
from PySide6.QtGui import QIcon

class UvGitInstallCard(WithExistedInstallCard):
    def __init__(self, ctx):
        super().__init__(
            ctx=ctx,
            title_cn='Git',
            install_method=self.uv_install_git,
            install_btn_icon=FluentIcon.DOWN,
            install_btn_text_cn='默认安装',
            content_cn='未安装'
        )
        self.ctx = ctx

    def uv_install_git(self, progress_callback):
        print('[uv_install_git] called')
        import shutil
        git_path = shutil.which('git')
        print(f'[uv_install_git] 环境变量检测git: {git_path}')
        if git_path and os.path.exists(git_path):
            self.ctx.env_config.git_path = git_path
            print('[uv_install_git] 环境变量已存在git，直接return')
            return True, gt('已检测到系统Git，无需安装', 'ui')
        def has_winget():
            try:
                result = subprocess.run(['winget', '--version'], capture_output=True, timeout=5)
                print(f'[uv_install_git] winget --version returncode: {result.returncode}')
                return result.returncode == 0
            except Exception as e:
                print(f'[uv_install_git] winget --version exception: {e}')
                return False
        if has_winget():
            print('[uv_install_git] winget detected, try install')
            if progress_callback:
                progress_callback(-1, gt('正在尝试用winget安装Git', 'ui'))
            try:
                result = subprocess.run(
                    ['winget', 'install', '--id', 'Git.Git', '-e', '--source', 'winget', '-h'],
                    timeout=120, capture_output=True, text=True
                )
                print(f'[uv_install_git] winget install returncode: {result.returncode}')
                print(f'[uv_install_git] winget stdout: {result.stdout}')
                print(f'[uv_install_git] winget stderr: {result.stderr}')
                git_path = shutil.which('git')
                print(f'[uv_install_git] shutil.which git: {git_path}')
                if git_path and os.path.exists(git_path):
                    self.ctx.env_config.git_path = git_path
                    print('[uv_install_git] winget安装Git后检测到git.exe，直接return')
                    return True, gt('winget安装Git成功', 'ui')
                else:
                    print('[uv_install_git] winget安装Git后未检测到git.exe')
                    return False, gt('winget安装Git后未检测到git.exe', 'ui')
            except Exception as e:
                print(f'[uv_install_git] winget安装Git异常: {e}')
                if progress_callback:
                    progress_callback(-1, gt('winget安装Git异常，尝试绿色版安装', 'ui') + str(e))
        print('[uv_install_git] fallback to 绿色版')
        if progress_callback:
            progress_callback(-1, gt('正在尝试绿色版安装Git', 'ui'))
        result = self.ctx.git_service.install_default_git(progress_callback)
        print(f'[uv_install_git] 绿色版安装Git result: {result}')
        if result[0]:
            git_path = DEFAULT_GIT_PATH
            if git_path and os.path.exists(git_path):
                self.ctx.env_config.git_path = git_path
            else:
                print('[uv_install_git] 绿色版安装Git后未检测到git.exe')
                return False, gt('绿色版安装Git后未检测到git.exe', 'ui')
        return result

    def get_display_content(self):
        git_path = shutil.which('git')
        if not git_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装Git', 'ui')
            return icon, msg
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = gt('已安装', 'ui') + ' ' + git_path
            return icon, msg 