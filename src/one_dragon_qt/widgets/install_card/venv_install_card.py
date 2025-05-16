from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor
from typing import Tuple, Optional
import os
import shutil

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.wtih_existed_install_card import WithExistedInstallCard
from one_dragon.utils.i18_utils import gt
from one_dragon.utils import cmd_utils
from one_dragon.utils.log_utils import log


class VenvInstallCard(WithExistedInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        # 根据uv路径是否存在来决定使用哪种安装方式
        uv_path = ctx.env_config.uv_path
        if uv_path and os.path.exists(uv_path):
            install_method = self.uv_install_requirements
        else:
            install_method = self.pip_install_requirements

        WithExistedInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='运行依赖',
            install_method=install_method,
            install_btn_icon=FluentIcon.DOWN,
            install_btn_text_cn='默认安装',
            content_cn='未安装'
        )

    def uv_install_requirements(self, progress_callback):
        if progress_callback:
            progress_callback(-1, gt('正在用uv安装依赖...', 'ui'))
        python_path = self.ctx.env_config.python_path
        if not python_path or not os.path.exists(python_path):
            return False, gt('未检测到虚拟环境python.exe', 'ui')
        venv_dir = os.path.dirname(os.path.dirname(python_path))
        
        try:
            # 设置环境变量
            os.environ["VIRTUAL_ENV"] = venv_dir
            os.environ["PATH"] = os.path.join(venv_dir, "Scripts") + os.pathsep + os.environ["PATH"]
            
            # 先确保 pip 已安装
            ensure_pip_cmd = [python_path, '-m', 'ensurepip', '--upgrade']
            cmd_utils.run_command(ensure_pip_cmd, cwd=venv_dir)

            # 使用uv安装
            uv_path = self.ctx.env_config.uv_path
            install_cmd = [uv_path, 'pip', 'install', '-r', 'requirements-prod.txt']
            result = cmd_utils.run_command(
                install_cmd,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result is None:
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

    def pip_install_requirements(self, progress_callback):
        if progress_callback:
            progress_callback(-1, gt('正在用pip安装依赖...', 'ui'))
        python_path = self.ctx.env_config.python_path
        if not python_path or not os.path.exists(python_path):
            return False, gt('未检测到虚拟环境python.exe', 'ui')
        venv_dir = os.path.dirname(os.path.dirname(python_path))
        
        try:
            # 设置环境变量
            os.environ["VIRTUAL_ENV"] = venv_dir
            os.environ["PATH"] = os.path.join(venv_dir, "Scripts") + os.pathsep + os.environ["PATH"]
            
            # 先确保 pip 已安装
            ensure_pip_cmd = [python_path, '-m', 'ensurepip', '--upgrade']
            cmd_utils.run_command(ensure_pip_cmd, cwd=venv_dir)

            # 使用pip安装
            install_cmd = [python_path, '-m', 'pip', 'install', '-r', 'requirements-prod.txt']
            result = cmd_utils.run_command(
                install_cmd,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
            if result is None:
                return False, gt('pip安装依赖失败', 'ui')
                
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
            log.error('pip安装依赖异常', exc_info=True)
            return False, gt('pip安装依赖异常', 'ui') + str(e)
            
        if progress_callback:
            progress_callback(1, gt('pip依赖安装成功', 'ui'))
        return True, gt('pip依赖安装成功', 'ui')

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        last = self.ctx.env_config.requirement_time

        if last != self.ctx.git_service.get_requirement_time():
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
            msg = gt('需更新，请使用安装器更新', 'ui')
        else:
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
            msg = f"{gt('已安装', 'ui')}" + ' ' + last

        return icon, msg
