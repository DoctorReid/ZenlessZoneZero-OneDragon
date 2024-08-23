from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton, ComboBox, PlainTextEdit, SubtitleLabel, BodyLabel, FluentThemeColor
from typing import List, Optional

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.multi_push_setting_card import MultiPushSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentEnum
from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig, \
    get_all_hollow_zero_challenge_config, get_hollow_zero_challenge_new_name


class HollowZeroChallengeConfigInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            object_name='hollow_zero_challenge_config_interface',
            parent=parent,
            content_widget=None,
            nav_text_cn='挑战配置'
        )

        self.chosen_config: Optional[HollowZeroChallengeConfig] = None

    def get_content_widget(self) -> QWidget:
        content_widget = RowWidget()

        content_widget.add_widget(self._init_left_part(), stretch=1)
        content_widget.add_widget(self._init_right_part(), stretch=1)

        return content_widget

    def _init_left_part(self) -> QWidget:
        widget = ColumnWidget()

        btn_row = RowWidget()
        widget.add_widget(btn_row)

        self.existed_yml_btn = ComboBox()
        self.existed_yml_btn.setPlaceholderText(gt('选择已有', 'ui'))
        btn_row.add_widget(self.existed_yml_btn)

        self.create_btn = PushButton(text=gt('新建', 'ui'))
        self.create_btn.clicked.connect(self._on_create_clicked)
        btn_row.add_widget(self.create_btn)

        self.copy_btn = PushButton(text=gt('复制', 'ui'))
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        btn_row.add_widget(self.copy_btn)

        self.delete_btn = PushButton(text=gt('删除', 'ui'))
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        btn_row.add_widget(self.delete_btn)

        self.cancel_btn = PushButton(text=gt('取消', 'ui'))
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_row.add_widget(self.cancel_btn)

        btn_row.add_stretch(1)

        self.error_message = BodyLabel(text='测试')
        self.error_message.setTextColor(FluentThemeColor.RED.value)
        widget.add_widget(self.error_message)

        self.name_opt = TextSettingCard(icon=FluentIcon.GAME, title='配置名称', content='样例配置复制后可修改')
        self.name_opt.value_changed.connect(self._on_name_changed)
        widget.add_widget(self.name_opt)

        self.agent_btn_list: List[ComboBox] = []
        for i in range(3):
            agent_btn = ComboBox()
            for agent_enum in AgentEnum:
                agent_btn.addItem(agent_enum.value.agent_name, userData=agent_enum.value.agent_id)
            agent_btn.currentIndexChanged.connect(self._on_agent_changed)
            self.agent_btn_list.append(agent_btn)

        self.agents_opt = MultiPushSettingCard(btn_list=self.agent_btn_list, icon=FluentIcon.PEOPLE,
                                               title='目标配队', content='超过3人配队进入空洞时才需要配置，呼叫增援时保留这3个')
        widget.add_widget(self.agents_opt)

        self.auto_battle_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='自动战斗')
        self.auto_battle_opt.value_changed.connect(self._on_auto_battle_config_changed)
        widget.add_widget(self.auto_battle_opt)

        widget.add_stretch(1)
        return widget

    def _init_right_part(self) -> QWidget:
        widget = ColumnWidget()

        resonium_title = SubtitleLabel(text='奖励优先级')
        widget.add_widget(resonium_title)
        self.resonium_priority_input = PlainTextEdit()
        self.resonium_priority_input.textChanged.connect(self._on_resonium_priority_changed)
        widget.add_widget(self.resonium_priority_input)

        event_priority_title = SubtitleLabel(text='选项优先级')
        widget.add_widget(event_priority_title)
        self.event_priority_input = PlainTextEdit()
        self.event_priority_input.textChanged.connect(self._on_event_priority_changed)
        widget.add_widget(self.event_priority_input)
        self.event_priority_input.setVisible(False)

        widget.add_stretch(1)

        return widget

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self._update_whole_display()

    def _update_whole_display(self) -> None:
        """
        根据画面图片，统一更新界面的显示
        :return:
        """
        chosen = self.chosen_config is not None
        is_sample = self.chosen_config is None or self.chosen_config.is_sample

        self.existed_yml_btn.setDisabled(chosen)
        self.create_btn.setDisabled(chosen)
        self.copy_btn.setDisabled(not chosen)
        self.delete_btn.setDisabled(not chosen or is_sample)
        self.cancel_btn.setDisabled(not chosen)

        self.name_opt.setDisabled(not chosen or is_sample)
        self.auto_battle_opt.setDisabled(not chosen or is_sample)
        self.agents_opt.setDisabled(not chosen or is_sample)
        for agent_btn in self.agent_btn_list:
            agent_btn.setDisabled(not chosen or is_sample)
        self.resonium_priority_input.setDisabled(not chosen or is_sample)
        self.event_priority_input.setDisabled(not chosen or is_sample)

        self._update_existed_yml_options()
        self._update_auto_battle_opts()

        if chosen:
            self.name_opt.setValue(self.chosen_config.module_name)
            self.auto_battle_opt.setValue(self.chosen_config.auto_battle)
            agents = self.chosen_config.target_agents
            for i in range(3):
                btn = self.agent_btn_list[i]
                if agents[i] is None:
                    btn.setCurrentIndex(-1)
                else:
                    btn.setCurrentIndex(btn.findData(agents[i]))
            self.resonium_priority_input.setPlainText(self.chosen_config.resonium_priority_str)
            self.event_priority_input.setPlainText(self.chosen_config.event_priority_str)

    def _update_existed_yml_options(self) -> None:
        """
        更新已有的yml选项
        :return:
        """
        try:
            # 更新之前 先取消原来的监听 防止触发事件
            self.existed_yml_btn.currentIndexChanged.disconnect(self._on_choose_existed_yml)
        except Exception:
            pass
        self.existed_yml_btn.clear()
        config_list: List[HollowZeroChallengeConfig] = get_all_hollow_zero_challenge_config()
        for config in config_list:
            self.existed_yml_btn.addItem(text=config.module_name, icon=None, userData=config)
        self.existed_yml_btn.setCurrentIndex(-1)
        self.existed_yml_btn.setPlaceholderText(gt('选择已有', 'ui'))
        self.existed_yml_btn.currentIndexChanged.connect(self._on_choose_existed_yml)

    def _update_auto_battle_opts(self) -> None:
        """
        自动战斗的配置下拉框
        :return:
        """
        try:
            self.auto_battle_opt.value_changed.disconnect(self._on_auto_battle_config_changed)
        except:
            pass
        self.auto_battle_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))
        self.auto_battle_opt.value_changed.connect(self._on_auto_battle_config_changed)

    def _on_choose_existed_yml(self, idx: int):
        """
        选择了已有的yml
        :param idx:
        :return:
        """
        self.chosen_config: HollowZeroChallengeConfig = self.existed_yml_btn.items[idx].userData
        self._update_whole_display()

    def _on_create_clicked(self):
        """
        创建一个新的
        :return:
        """
        if self.chosen_config is not None:
            return

        self.chosen_config = HollowZeroChallengeConfig(get_hollow_zero_challenge_new_name(), False)
        self.chosen_config.remove_sample()

        self._update_whole_display()

    def _on_copy_clicked(self):
        """
        复制一个
        :return:
        """
        if self.chosen_config is None:
            return

        self.chosen_config.copy_new()
        self._update_whole_display()

    def _on_save_clicked(self) -> None:
        """
        保存配置
        :return:
        """
        if self.chosen_config is None:
            return

        self.chosen_config.save()
        self._update_existed_yml_options()

    def _on_delete_clicked(self) -> None:
        """
        删除
        :return:
        """
        if self.chosen_config is None:
            return
        self.chosen_config.delete()
        self.chosen_config = None
        self._update_whole_display()

    def _on_cancel_clicked(self) -> None:
        """
        取消编辑
        :return:
        """
        if self.chosen_config is None:
            return
        self.chosen_config = None
        self.existed_yml_btn.setCurrentIndex(-1)
        self._update_whole_display()

    def _on_name_changed(self, value: str) -> None:
        if self.chosen_config is None:
            return

        self.chosen_config.module_name = value
        self.chosen_config.save()

    def _on_auto_battle_config_changed(self, index, value) -> None:
        if self.chosen_config is None:
            return

        self.chosen_config.auto_battle = value

    def _update_error_message(self, msg: str) -> None:
        if msg is None or len(msg) == 0:
            self.error_message.setVisible(False)
        else:
            self.error_message.setText(msg)
            self.error_message.setVisible(True)

    def _on_resonium_priority_changed(self) -> None:
        if self.chosen_config is None:
            return

        value = self.resonium_priority_input.toPlainText()
        priority_list, err_msg = self.ctx.hollow.data_service.check_resonium_priority(value)
        self._update_error_message(err_msg)

        self.chosen_config.resonium_priority = priority_list

    def _on_event_priority_changed(self) -> None:
        if self.chosen_config is None:
            return

        value = self.event_priority_input.toPlainText()

        self.chosen_config.event_priority = [i.strip() for i in value.split('\n')]

    def _on_agent_changed(self, idx: int) -> None:
        if self.chosen_config is None:
            return

        agents = []
        for i in range(3):
            if self.agent_btn_list[i].currentIndex() == -1:
                agents.append(None)
            else:
                agents.append(self.agent_btn_list[i].currentData())

        self.chosen_config.target_agents = agents