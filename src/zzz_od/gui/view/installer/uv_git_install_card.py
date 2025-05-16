from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
from one_dragon.utils import cmd_utils
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

    def on_existed_chosen(self, file_path: str) -> None:
        """
        选择了本地文件之后的回调
        :param file_path: 本地文件的路径
        :return:
        """
        self.ctx.env_config.git_path = file_path  # 这会通过 setter 自动保存配置
        self.check_and_update_display()  # 更新卡片显示内容
        self.finished.emit(True)  # 发射完成信号

    def uv_install_git(self, progress_callback):
        print('[uv_install_git] called')
        # 移除自动查找功能，直接尝试安装
        def has_winget():
            try:
                result = cmd_utils.run_command(['winget', '--version'])
                print(f'[uv_install_git] winget --version result: {result}')
                return result is not None
            except Exception as e:
                print(f'[uv_install_git] winget --version exception: {e}')
                return False
                
        if has_winget():
            print('[uv_install_git] winget detected, try install')
            if progress_callback:
                progress_callback(-1, gt('正在尝试用winget安装Git', 'ui'))
            try:
                result = cmd_utils.run_command(
                    ['winget', 'install', '--id', 'Git.Git', '-e', '--source', 'winget', '-h']
                )
                print(f'[uv_install_git] winget install result: {result}')
                git_path = shutil.which('git')
                print(f'[uv_install_git] shutil.which git: {git_path}')
                if git_path and os.path.exists(git_path):
                    # 检测 Git 是否可用
                    try:
                        result = cmd_utils.run_command([git_path, '--version'])
                        if result:
                            self.ctx.env_config.git_path = git_path
                            print('[uv_install_git] winget安装Git后检测到git.exe且可用，直接return')
                            return True, gt('winget安装Git成功', 'ui')
                        else:
                            print('[uv_install_git] winget安装Git后git --version 返回为空，可能不可用')
                    except Exception as e:
                        print(f'[uv_install_git] winget安装Git后git --version 异常: {e}')
                    print('[uv_install_git] winget安装Git后git不可用')
                    return False, gt('winget安装Git后Git不可用', 'ui')
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
                # 检测 Git 是否可用
                try:
                    result = cmd_utils.run_command([git_path, '--version'])
                    if result:
                        self.ctx.env_config.git_path = git_path
                        print('[uv_install_git] 绿色版安装Git后检测到git.exe且可用')
                    else:
                        print('[uv_install_git] 绿色版安装Git后git --version 返回为空，可能不可用')
                        return False, gt('绿色版安装Git后Git不可用', 'ui')
                except Exception as e:
                    print(f'[uv_install_git] 绿色版安装Git后git --version 异常: {e}')
                    return False, gt('绿色版安装Git后Git不可用', 'ui')
            else:
                print('[uv_install_git] 绿色版安装Git后未检测到git.exe')
                return False, gt('绿色版安装Git后未检测到git.exe', 'ui')
        return result

    def get_display_content(self):
        git_path = self.ctx.env_config.git_path
        if not git_path:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装Git', 'ui')
            return icon, msg
        elif not os.path.exists(git_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('文件不存在', 'ui') + ' ' + git_path
            return icon, msg
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = gt('已安装', 'ui') + ' ' + git_path
            return icon, msg

    def get_existed_os_path(self):
        """
        获取系统环境变量中的路径
        """
        return self.ctx.git_service.get_os_git_path() 