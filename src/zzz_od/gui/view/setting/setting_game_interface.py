import os
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import SettingCardGroup, FluentIcon, PushSettingCard

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.controller.pc_button.ds4_button_controller import Ds4ButtonEnum
from one_dragon.base.controller.pc_button.xbox_button_controller import XboxButtonEnum
from one_dragon.gui.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.widgets.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon.gui.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from phosdeiz.gui.widgets import Column
from zzz_od.config.game_config import GameRegionEnum, GamepadTypeEnum, TypeInputWay
from zzz_od.context.zzz_context import ZContext


class SettingGameInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_game_interface',
            content_widget=None, parent=parent,
            nav_text_cn='游戏设置'
        )
        self.ctx: ZContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        content_widget.add_widget(self._get_basic_group())
        content_widget.add_widget(self._get_key_group())
        content_widget.add_widget(self._get_gamepad_group())
        content_widget.add_stretch(1)

        return content_widget

    def _get_basic_group(self) -> QWidget:
        basic_group = SettingCardGroup(gt('游戏基础', 'ui'))

        self.game_path_opt = PushSettingCard(icon=FluentIcon.FOLDER, title='游戏路径', text='选择')
        self.game_path_opt.clicked.connect(self._on_game_path_clicked)
        basic_group.addSettingCard(self.game_path_opt)

        self.game_region_opt = ComboBoxSettingCard(icon=FluentIcon.HOME, title='游戏区服', options_enum=GameRegionEnum)
        self.game_region_opt.value_changed.connect(self._on_game_region_changed)
        basic_group.addSettingCard(self.game_region_opt)

        self.game_account_opt = TextSettingCard(icon=FluentIcon.PEOPLE, title='账号')
        basic_group.addSettingCard(self.game_account_opt)

        self.game_password_opt = TextSettingCard(icon=FluentIcon.EXPRESSIVE_INPUT_ENTRY, title='密码',
                                                 content='放心不会盗你的号 异地登陆需要验证')
        basic_group.addSettingCard(self.game_password_opt)

        self.input_way_opt = ComboBoxSettingCard(icon=FluentIcon.CLIPPING_TOOL, title='输入方式',
                                                 options_enum=TypeInputWay)
        basic_group.addSettingCard(self.input_way_opt)

        return basic_group

    def _get_key_group(self) -> QWidget:
        key_group = SettingCardGroup(gt('游戏按键', 'ui'))

        self.key_normal_attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='普通攻击')
        key_group.addSettingCard(self.key_normal_attack_opt)

        self.key_dodge_opt = KeySettingCard(icon=FluentIcon.GAME, title='闪避')
        key_group.addSettingCard(self.key_dodge_opt)

        self.key_switch_next_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-下一个')
        key_group.addSettingCard(self.key_switch_next_opt)

        self.key_switch_prev_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-上一个')
        key_group.addSettingCard(self.key_switch_prev_opt)

        self.key_special_attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='特殊攻击')
        key_group.addSettingCard(self.key_special_attack_opt)

        self.key_ultimate_opt = KeySettingCard(icon=FluentIcon.GAME, title='终结技')
        key_group.addSettingCard(self.key_ultimate_opt)

        self.key_interact_opt = KeySettingCard(icon=FluentIcon.GAME, title='交互')
        key_group.addSettingCard(self.key_interact_opt)

        self.key_chain_left_opt = KeySettingCard(icon=FluentIcon.GAME, title='连携技-左')
        key_group.addSettingCard(self.key_chain_left_opt)

        self.key_chain_right_opt = KeySettingCard(icon=FluentIcon.GAME, title='连携技-右')
        key_group.addSettingCard(self.key_chain_right_opt)

        self.key_move_w_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-前')
        key_group.addSettingCard(self.key_move_w_opt)

        self.key_move_s_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-后')
        key_group.addSettingCard(self.key_move_s_opt)

        self.key_move_a_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-左')
        key_group.addSettingCard(self.key_move_a_opt)

        self.key_move_d_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-右')
        key_group.addSettingCard(self.key_move_d_opt)

        self.key_lock_opt = KeySettingCard(icon=FluentIcon.GAME, title='锁定敌人')
        key_group.addSettingCard(self.key_lock_opt)

        self.key_chain_cancel_opt = KeySettingCard(icon=FluentIcon.GAME, title='连携技-取消')
        key_group.addSettingCard(self.key_chain_cancel_opt)

        return key_group

    def _get_gamepad_group(self) -> QWidget:
        gamepad_group = SettingCardGroup(gt('手柄按键', 'ui'))

        self.gamepad_type_opt = ComboBoxSettingCard(
            icon=FluentIcon.GAME, title='手柄类型',
            content='需先安装虚拟手柄依赖，参考文档或使用安装器。仅在闪避助手生效。',
            options_enum=GamepadTypeEnum
        )
        self.gamepad_type_opt.value_changed.connect(self._on_gamepad_type_changed)
        gamepad_group.addSettingCard(self.gamepad_type_opt)

        # xbox
        self.xbox_key_press_time_opt = TextSettingCard(icon=FluentIcon.GAME, title='单次按键持续时间(秒)',
                                                       content='自行调整，过小可能按键被吞，过大可能影响操作')
        gamepad_group.addSettingCard(self.xbox_key_press_time_opt)

        self.xbox_key_normal_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='普通攻击', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_normal_attack_opt)

        self.xbox_key_dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_dodge_opt)

        self.xbox_key_switch_next_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-下一个', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_switch_next_opt)

        self.xbox_key_switch_prev_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-上一个', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_switch_prev_opt)

        self.xbox_key_special_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='特殊攻击', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_special_attack_opt)

        self.xbox_key_ultimate_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='终结技', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_ultimate_opt)

        self.xbox_key_interact_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='交互', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_interact_opt)

        self.xbox_key_chain_left_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-左', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_chain_left_opt)

        self.xbox_key_chain_right_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-右', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_chain_right_opt)

        self.xbox_key_move_w_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-前', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_move_w_opt)

        self.xbox_key_move_s_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-后', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_move_s_opt)

        self.xbox_key_move_a_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-左', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_move_a_opt)

        self.xbox_key_move_d_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-右', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_move_d_opt)

        self.xbox_key_lock_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='锁定敌人', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_lock_opt)

        self.xbox_key_chain_cancel_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-取消', options_enum=XboxButtonEnum)
        gamepad_group.addSettingCard(self.xbox_key_chain_cancel_opt)

        # ds4
        self.ds4_key_press_time_opt = TextSettingCard(icon=FluentIcon.GAME, title='单次按键持续时间(秒)',
                                                      content='自行调整，过小可能按键被吞，过大可能影响操作')
        gamepad_group.addSettingCard(self.ds4_key_press_time_opt)

        self.ds4_key_normal_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='普通攻击', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_normal_attack_opt)

        self.ds4_key_dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_dodge_opt)

        self.ds4_key_switch_next_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-下一个', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_switch_next_opt)

        self.ds4_key_switch_prev_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-上一个', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_switch_prev_opt)

        self.ds4_key_special_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='特殊攻击', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_special_attack_opt)

        self.ds4_key_ultimate_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='终结技', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_ultimate_opt)

        self.ds4_key_interact_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='交互', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_interact_opt)

        self.ds4_key_chain_left_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-左', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_chain_left_opt)

        self.ds4_key_chain_right_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-右', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_chain_right_opt)

        self.ds4_key_move_w_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-前', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_move_w_opt)

        self.ds4_key_move_s_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-后', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_move_s_opt)

        self.ds4_key_move_a_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-左', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_move_a_opt)

        self.ds4_key_move_d_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-右', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_move_d_opt)

        self.ds4_key_lock_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='锁定敌人', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_lock_opt)

        self.ds4_key_chain_cancel_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-取消', options_enum=Ds4ButtonEnum)
        gamepad_group.addSettingCard(self.ds4_key_chain_cancel_opt)

        return gamepad_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.game_region_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('game_region'))
        self.game_account_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('account'))
        self.game_password_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('password'))

        self.game_path_opt.setContent(self.ctx.game_config.game_path)
        self.input_way_opt.init_with_adapter(self.ctx.game_config.type_input_way_adapter)

        self.key_normal_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_normal_attack'))
        self.key_dodge_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_dodge'))
        self.key_switch_next_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_switch_next'))
        self.key_switch_prev_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_switch_prev'))
        self.key_special_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_special_attack'))
        self.key_ultimate_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_ultimate'))
        self.key_interact_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_interact'))
        self.key_chain_left_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_chain_left'))
        self.key_chain_right_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_chain_right'))
        self.key_move_w_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_move_w'))
        self.key_move_s_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_move_s'))
        self.key_move_a_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_move_a'))
        self.key_move_d_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_move_d'))
        self.key_lock_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_lock'))
        self.key_chain_cancel_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('key_chain_cancel'))

        self._update_gamepad_part()

    def _update_gamepad_part(self) -> None:
        """
        手柄部分更新显示
        :return:
        """
        self.gamepad_type_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('gamepad_type'))

        is_xbox = self.ctx.game_config.gamepad_type == GamepadTypeEnum.XBOX.value.value

        self.xbox_key_press_time_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_press_time', 'str', 'float'))
        self.xbox_key_normal_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_normal_attack'))
        self.xbox_key_dodge_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_dodge'))
        self.xbox_key_switch_next_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_switch_next'))
        self.xbox_key_switch_prev_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_switch_prev'))
        self.xbox_key_special_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_special_attack'))
        self.xbox_key_ultimate_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_ultimate'))
        self.xbox_key_interact_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_interact'))
        self.xbox_key_chain_left_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_chain_left'))
        self.xbox_key_chain_right_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_chain_right'))
        self.xbox_key_move_w_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_move_w'))
        self.xbox_key_move_s_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_move_s'))
        self.xbox_key_move_a_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_move_a'))
        self.xbox_key_move_d_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_move_d'))
        self.xbox_key_lock_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_lock'))
        self.xbox_key_chain_cancel_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('xbox_key_chain_cancel'))

        self.xbox_key_press_time_opt.setVisible(is_xbox)
        self.xbox_key_normal_attack_opt.setVisible(is_xbox)
        self.xbox_key_dodge_opt.setVisible(is_xbox)
        self.xbox_key_switch_next_opt.setVisible(is_xbox)
        self.xbox_key_switch_prev_opt.setVisible(is_xbox)
        self.xbox_key_special_attack_opt.setVisible(is_xbox)
        self.xbox_key_ultimate_opt.setVisible(is_xbox)
        self.xbox_key_interact_opt.setVisible(is_xbox)
        self.xbox_key_chain_left_opt.setVisible(is_xbox)
        self.xbox_key_chain_right_opt.setVisible(is_xbox)
        self.xbox_key_move_w_opt.setVisible(is_xbox)
        self.xbox_key_move_s_opt.setVisible(is_xbox)
        self.xbox_key_move_a_opt.setVisible(is_xbox)
        self.xbox_key_move_d_opt.setVisible(is_xbox)
        self.xbox_key_lock_opt.setVisible(is_xbox)
        self.xbox_key_chain_cancel_opt.setVisible(is_xbox)

        is_ds4 = self.ctx.game_config.gamepad_type == GamepadTypeEnum.DS4.value.value

        self.ds4_key_press_time_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_press_time', 'str', 'float'))
        self.ds4_key_normal_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_normal_attack'))
        self.ds4_key_dodge_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_dodge'))
        self.ds4_key_switch_next_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_switch_next'))
        self.ds4_key_switch_prev_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_switch_prev'))
        self.ds4_key_special_attack_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_special_attack'))
        self.ds4_key_ultimate_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_ultimate'))
        self.ds4_key_interact_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_interact'))
        self.ds4_key_chain_left_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_chain_left'))
        self.ds4_key_chain_right_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_chain_right'))
        self.ds4_key_move_w_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_move_w'))
        self.ds4_key_move_s_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_move_s'))
        self.ds4_key_move_a_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_move_a'))
        self.ds4_key_move_d_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_move_d'))
        self.ds4_key_lock_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_lock'))
        self.ds4_key_chain_cancel_opt.init_with_adapter(self.ctx.game_config.get_prop_adapter('ds4_key_chain_cancel'))

        self.ds4_key_press_time_opt.setVisible(is_ds4)
        self.ds4_key_normal_attack_opt.setVisible(is_ds4)
        self.ds4_key_dodge_opt.setVisible(is_ds4)
        self.ds4_key_switch_next_opt.setVisible(is_ds4)
        self.ds4_key_switch_prev_opt.setVisible(is_ds4)
        self.ds4_key_special_attack_opt.setVisible(is_ds4)
        self.ds4_key_ultimate_opt.setVisible(is_ds4)
        self.ds4_key_interact_opt.setVisible(is_ds4)
        self.ds4_key_chain_left_opt.setVisible(is_ds4)
        self.ds4_key_chain_right_opt.setVisible(is_ds4)
        self.ds4_key_move_w_opt.setVisible(is_ds4)
        self.ds4_key_move_s_opt.setVisible(is_ds4)
        self.ds4_key_move_a_opt.setVisible(is_ds4)
        self.ds4_key_move_d_opt.setVisible(is_ds4)
        self.ds4_key_lock_opt.setVisible(is_ds4)
        self.ds4_key_chain_cancel_opt.setVisible(is_ds4)

    def _on_game_region_changed(self, index, value):
        self.ctx.init_by_config()

    def _on_game_path_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, gt('选择你的 ZenlessZoneZero.exe'), filter="Exe (*.exe)")
        if file_path is not None and file_path.endswith('.exe'):
            log.info('选择路径 %s', file_path)
            self._on_game_path_chosen(os.path.normpath(file_path))

    def _on_game_path_chosen(self, file_path) -> None:
        self.ctx.game_config.game_path = file_path
        self.game_path_opt.setContent(file_path)

    def _on_gamepad_type_changed(self, idx: int, value: str) -> None:
        self._update_gamepad_part()
