from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, PushButton, PlainTextEdit, SubtitleLabel, BodyLabel, FluentThemeColor
from typing import List, Optional

from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from phosdeiz.gui.widgets import Column, ComboBox, Row
from zzz_od.application.battle_assistant.auto_battle_config import get_auto_battle_op_config_list
from zzz_od.application.hollow_zero.lost_void.lost_void_challenge_config import LostVoidChallengeConfig, \
    get_lost_void_challenge_new_name, get_all_lost_void_challenge_config
from zzz_od.context.zzz_context import ZContext


class LostVoidChallengeConfigInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        VerticalScrollInterface.__init__(
            self,
            object_name='lost_void_challenge_config_interface',
            parent=parent,
            content_widget=None,
            nav_text_cn='挑战配置-迷'
        )

        self.ctx: ZContext = ctx
        self.chosen_config: Optional[LostVoidChallengeConfig] = None

    def get_content_widget(self) -> QWidget:
        content_widget = Row()

        content_widget.add_widget(self._init_left_part(), stretch=1)
        content_widget.add_widget(self._init_right_part(), stretch=1)

        return content_widget

    def _init_left_part(self) -> QWidget:
        widget = Column()

        btn_row = Row()
        widget.add_widget(btn_row)

        self.existed_yml_btn = ComboBox()
        self.existed_yml_btn.setPlaceholderText(gt('选择已有', 'ui'))
        self.existed_yml_btn.currentIndexChanged.connect(self._on_choose_existed_yml)
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

        self.error_message = BodyLabel(text='')
        self.error_message.setTextColor(FluentThemeColor.RED.value)
        widget.add_widget(self.error_message)

        self.name_opt = TextSettingCard(icon=FluentIcon.GAME, title='配置名称', content='默认配置复制后可修改')
        self.name_opt.value_changed.connect(self._on_name_changed)
        widget.add_widget(self.name_opt)

        self.auto_battle_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='自动战斗')
        self.auto_battle_opt.value_changed.connect(self._on_auto_battle_config_changed)
        widget.add_widget(self.auto_battle_opt)

        widget.add_stretch(1)
        return widget

    def _init_right_part(self) -> QWidget:
        widget = Column()

        artifact_priority_widget = Column()
        widget.add_widget(artifact_priority_widget)
        artifact_priority_title = SubtitleLabel(text='藏品优先级')
        artifact_priority_widget.v_layout.addWidget(artifact_priority_title)
        self.artifact_priority_input = PlainTextEdit()
        self.artifact_priority_input.textChanged.connect(self._on_artifact_priority_changed)
        artifact_priority_widget.v_layout.addWidget(self.artifact_priority_input)

        region_priority_widget = Column()
        widget.add_widget(region_priority_widget)
        region_priority_title = SubtitleLabel(text='区域类型优先级 未生效')
        region_priority_widget.v_layout.addWidget(region_priority_title)
        self.region_type_priority_input = PlainTextEdit()
        self.region_type_priority_input.textChanged.connect(self._on_region_type_priority_changed)
        region_priority_widget.v_layout.addWidget(self.region_type_priority_input)

        widget.add_stretch(1)

        return widget

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self.ctx.lost_void.load_artifact_data()
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
        self.artifact_priority_input.setDisabled(not chosen or is_sample)
        self.region_type_priority_input.setDisabled(not chosen or is_sample)

        self._update_existed_yml_options()
        self.auto_battle_opt.set_options_by_list(get_auto_battle_op_config_list('auto_battle'))

        if chosen:
            self.name_opt.setValue(self.chosen_config.module_name)
            self.auto_battle_opt.setValue(self.chosen_config.auto_battle)

            self.artifact_priority_input.blockSignals(True)
            self.artifact_priority_input.setPlainText(self.chosen_config.artifact_priority_str)
            self.artifact_priority_input.blockSignals(False)

            self.region_type_priority_input.blockSignals(True)
            self.region_type_priority_input.setPlainText(self.chosen_config.region_type_priority_str)
            self.region_type_priority_input.blockSignals(False)

        if is_sample:
            self._update_error_message('当前为默认配置，点击复制后可修改')
        else:
            self._update_error_message('')

    def _update_existed_yml_options(self) -> None:
        """
        更新已有的yml选项
        :return:
        """
        self.existed_yml_btn.blockSignals(True)
        self.existed_yml_btn.clear()
        config_list: List[LostVoidChallengeConfig] = get_all_lost_void_challenge_config()
        for config in config_list:
            self.existed_yml_btn.addItem(text=config.module_name, icon=None, userData=config)
        self.existed_yml_btn.setCurrentIndex(-1)
        self.existed_yml_btn.setPlaceholderText(gt('选择已有', 'ui'))
        self.existed_yml_btn.blockSignals(False)

    def _on_choose_existed_yml(self, idx: int):
        """
        选择了已有的yml
        :param idx:
        :return:
        """
        self.chosen_config: LostVoidChallengeConfig = self.existed_yml_btn.items[idx].userData
        self._update_whole_display()

    def _on_create_clicked(self):
        """
        创建一个新的
        :return:
        """
        if self.chosen_config is not None:
            return

        self.chosen_config = LostVoidChallengeConfig(get_lost_void_challenge_new_name(), False)
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

        self.chosen_config.update_module_name(value)

    def _on_buy_only_priority_changed(self, value: bool):
        if self.chosen_config is None:
            return
        self.chosen_config.buy_only_priority = value

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

    def _on_artifact_priority_changed(self) -> None:
        if self.chosen_config is None:
            return

        value = self.artifact_priority_input.toPlainText()
        entry_list, err_msg = self.ctx.lost_void.check_artifact_priority_input(value)
        self._update_error_message(err_msg)

        self.chosen_config.artifact_priority = entry_list

    def _on_region_type_priority_changed(self) -> None:
        if self.chosen_config is None:
            return

        value = self.region_type_priority_input.toPlainText()
        entry_list, err_msg = self.ctx.lost_void.check_region_type_priority_input(value)
        self._update_error_message(err_msg)

        self.chosen_config.region_priority = entry_list
