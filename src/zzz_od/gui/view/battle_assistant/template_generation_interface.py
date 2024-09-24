import os.path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton, PushSettingCard
from typing import Optional

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.view.app_run_interface import AppRunInterface
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.action_recorder.monitor import RecordContext
from zzz_od.action_recorder.template_generator import PreProcessor, SelfAdaptiveGenerator
from one_dragon.utils.log_utils import log


class TemplateGenerationInterface(AppRunInterface):

    def __init__(self,
                 ctx: ZContext,
                 parent=None):
        self.ctx: ZContext = ctx

        AppRunInterface.__init__(
            self,
            ctx=ctx,
            object_name='template_generation_interface',
            nav_text_cn='模板生成Beta',
            nav_icon=FluentIcon.GAME,
            parent=parent,
        )

        self.rc_ctx = None

    def get_widget_at_bottom(self) -> QWidget:
        bottom_widget = ColumnWidget()

        self.gen_opt = PushSettingCard(
            icon=FluentIcon.DOWN,
            title='生成模板',
            content='录制后，根据临时储存在 .log 文件夹的动作和状态文件，在 .log 文件夹中生成名为"配队动作模板.yml"的YAML模板',
            text='生成'
        )
        self.gen_opt.clicked.connect(self._template_generation)
        bottom_widget.add_widget(self.gen_opt)

        return bottom_widget

    def on_interface_shown(self) -> None:
        """
        界面显示时 进行初始化
        :return:
        """
        AppRunInterface.on_interface_shown(self)

    def _template_generation(self) -> None:
        """
        根据记录生成模板
        :return:
        """
        try:
            pp = PreProcessor()  # 预处理
            merged_status_ops = pp.pre_process()

            sag = SelfAdaptiveGenerator(merged_status_ops, pp.agent_names)  # 模板生成
            agent_templates, special_status = sag.get_templates()
            sag.output_yaml(agent_templates, special_status)

            msg = '模板生成成功, 请在.log文件夹内查看'
            log.error(msg)
        except:
            msg = '动作-状态记录未录制或存在格式错误'
            log.error(msg)

    def _on_start_clicked(self) -> None:
        # 开始录制
        self.ctx.init_by_config()
        self.ctx.ocr.init_model()

        self.rc_ctx = RecordContext(self.ctx)
        self.rc_ctx.records_status_and_action()
        self.rc_ctx.output_records()

    def _on_stop_clicked(self) -> None:
        self.rc_ctx.battle.last_check_end_result = True

        self.rc_ctx.button_listener.stop()
        self.rc_ctx.battle.stop_context()

        self.ctx.stop_running()

    def get_app(self) -> ZApplication:
        pass
