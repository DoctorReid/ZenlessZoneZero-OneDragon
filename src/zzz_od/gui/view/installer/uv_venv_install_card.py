from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from qfluentwidgets import FluentIcon, FluentThemeColor
from one_dragon.utils import cmd_utils
import os
from one_dragon.utils.i18_utils import gt
from PySide6.QtGui import QIcon
from one_dragon.utils.log_utils import log
from one_dragon.utils import os_utils

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
        log.info(f"Current python_path from config for requirements install: {python_path}")
        if not python_path or not os.path.exists(python_path):
            return False, gt('未检测到虚拟环境python.exe', 'ui')
        venv_dir = os.path.dirname(os.path.dirname(python_path))
        log.info(f"Deduced venv_dir for uv requirements install: {venv_dir}")
        
        # 使用 os_utils.get_work_dir() 获取正确的工作目录
        requirements = self.ctx.project_config.requirements
        req_path = os.path.join(os_utils.get_work_dir(), requirements)
        log.info(f"Requirements file path: {req_path}")
        
        if not os.path.exists(req_path):
            log.error(f"Requirements file not found at: {req_path}")
            return False, gt('未找到requirements文件', 'ui')
            
        try:
            # 设置环境变量
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = venv_dir
            env["PATH"] = os.path.join(venv_dir, "Scripts") + os.pathsep + env["PATH"]
            
            # 先升级pip
            upgrade_pip_cmd = [
                'uv', 'pip', 'install', '--upgrade', 'pip',
                '--index-url', self.ctx.env_config.pip_source,
                '--trusted-host', self.ctx.env_config.pip_trusted_host
            ]
            log.info(f"Running command: {' '.join(upgrade_pip_cmd)}")
            result = cmd_utils.run_command(
                upgrade_pip_cmd,
                cwd=venv_dir
            )
            if result is None:
                log.error("Upgrade pip failed")
                return False, gt('升级pip失败', 'ui')
            
            # 安装依赖
            install_cmd = [
                'uv', 'pip', 'install', '--upgrade',
                '-r', req_path,
                '--index-url', self.ctx.env_config.pip_source,
                '--trusted-host', self.ctx.env_config.pip_trusted_host
            ]
            log.info(f"Running command: {' '.join(install_cmd)}")
            result = cmd_utils.run_command(
                install_cmd,
                cwd=venv_dir
            )
            if result is None:
                log.error("Install requirements failed")
                return False, gt('uv安装依赖失败', 'ui')
                
            # 验证安装结果
            verify_cmd = [python_path, '-m', 'pip', 'list']
            verify_result = cmd_utils.run_command(
                verify_cmd,
                cwd=venv_dir
            )
            if verify_result:
                log.info(f"Installed packages:\n{verify_result}")
                
            # 更新requirement_time
            self.ctx.env_config.requirement_time = self.ctx.git_service.get_requirement_time()
            
        except Exception as e:
            log.error('uv安装依赖异常', exc_info=True)
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