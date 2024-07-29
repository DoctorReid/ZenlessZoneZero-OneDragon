from PySide6.QtWidgets import QWidget
from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.base.controller.pc_button.ds4_button_controller import Ds4ButtonEnum
from one_dragon.base.controller.pc_button.xbox_button_controller import XboxButtonEnum
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils.i18_utils import gt
from zzz_od.config.game_config import GameRegionEnum, GamepadTypeEnum
from zzz_od.context.zzz_context import ZContext


class SettingGameInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            object_name='setting_game_interface',
            content_widget=None, parent=parent,
            nav_text_cn='游戏设置'
        )

    def get_content_widget(self) -> QWidget:
        content_widget = ColumnWidget()

        content_widget.add_widget(self._get_basic_group())
        content_widget.add_widget(self._get_key_group())
        content_widget.add_widget(self._get_gamepad_group())
        content_widget.add_stretch(1)

        return content_widget

    def _get_basic_group(self) -> QWidget:
        basic_group = SettingCardGroup(gt('游戏基础', 'ui'))

        self.game_region_opt = ComboBoxSettingCard(icon=FluentIcon.HOME, title='游戏区服', options_enum=GameRegionEnum)
        self.game_region_opt.value_changed.connect(self._on_game_region_changed)
        basic_group.addSettingCard(self.game_region_opt)

        return basic_group

    def _get_key_group(self) -> QWidget:
        key_group = SettingCardGroup(gt('游戏按键', 'ui'))

        self.key_normal_attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='普通攻击')
        self.key_normal_attack_opt.value_changed.connect(self._on_key_normal_attack_changed)
        key_group.addSettingCard(self.key_normal_attack_opt)

        self.key_dodge_opt = KeySettingCard(icon=FluentIcon.GAME, title='闪避')
        self.key_dodge_opt.value_changed.connect(self._on_key_dodge_changed)
        key_group.addSettingCard(self.key_dodge_opt)

        self.key_switch_next_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-下一个')
        self.key_switch_next_opt.value_changed.connect(self._on_key_switch_next_changed)
        key_group.addSettingCard(self.key_switch_next_opt)

        self.key_switch_prev_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-上一个')
        self.key_switch_prev_opt.value_changed.connect(self._on_key_switch_prev_changed)
        key_group.addSettingCard(self.key_switch_prev_opt)

        self.key_special_attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='特殊攻击')
        self.key_special_attack_opt.value_changed.connect(self._on_key_special_attack_changed)
        key_group.addSettingCard(self.key_special_attack_opt)

        self.key_ultimate_opt = KeySettingCard(icon=FluentIcon.GAME, title='终结技')
        self.key_ultimate_opt.value_changed.connect(self._on_key_ultimate_changed)
        key_group.addSettingCard(self.key_ultimate_opt)

        self.key_interact_opt = KeySettingCard(icon=FluentIcon.GAME, title='交互')
        self.key_interact_opt.value_changed.connect(self._on_key_interact_changed)
        key_group.addSettingCard(self.key_interact_opt)

        self.key_chain_left_opt = KeySettingCard(icon=FluentIcon.GAME, title='连携技-左')
        self.key_chain_left_opt.value_changed.connect(self._on_key_chain_left_changed)
        key_group.addSettingCard(self.key_chain_left_opt)

        self.key_chain_right_opt = KeySettingCard(icon=FluentIcon.GAME, title='连携技-右')
        self.key_chain_right_opt.value_changed.connect(self._on_key_chain_right_changed)
        key_group.addSettingCard(self.key_chain_right_opt)

        self.key_move_w_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-前')
        self.key_move_w_opt.value_changed.connect(self._on_key_move_w_changed)
        key_group.addSettingCard(self.key_move_w_opt)

        self.key_move_s_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-后')
        self.key_move_s_opt.value_changed.connect(self._on_key_move_s_changed)
        key_group.addSettingCard(self.key_move_s_opt)

        self.key_move_a_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-左')
        self.key_move_a_opt.value_changed.connect(self._on_key_move_a_changed)
        key_group.addSettingCard(self.key_move_a_opt)

        self.key_move_d_opt = KeySettingCard(icon=FluentIcon.GAME, title='移动-右')
        self.key_move_d_opt.value_changed.connect(self._on_key_move_d_changed)
        key_group.addSettingCard(self.key_move_d_opt)

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
        self.xbox_key_press_time_opt.value_changed.connect(self._on_xbox_key_press_time_changed)
        gamepad_group.addSettingCard(self.xbox_key_press_time_opt)

        self.xbox_key_normal_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='普通攻击', options_enum=XboxButtonEnum)
        self.xbox_key_normal_attack_opt.value_changed.connect(self._on_xbox_key_normal_attack_changed)
        gamepad_group.addSettingCard(self.xbox_key_normal_attack_opt)

        self.xbox_key_dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避', options_enum=XboxButtonEnum)
        self.xbox_key_dodge_opt.value_changed.connect(self._on_xbox_key_dodge_changed)
        gamepad_group.addSettingCard(self.xbox_key_dodge_opt)

        self.xbox_key_switch_next_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-下一个', options_enum=XboxButtonEnum)
        self.xbox_key_switch_next_opt.value_changed.connect(self._on_xbox_key_switch_next_changed)
        gamepad_group.addSettingCard(self.xbox_key_switch_next_opt)

        self.xbox_key_switch_prev_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-上一个', options_enum=XboxButtonEnum)
        self.xbox_key_switch_prev_opt.value_changed.connect(self._on_xbox_key_switch_prev_changed)
        gamepad_group.addSettingCard(self.xbox_key_switch_prev_opt)

        self.xbox_key_special_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='特殊攻击', options_enum=XboxButtonEnum)
        self.xbox_key_special_attack_opt.value_changed.connect(self._on_xbox_key_special_attack_changed)
        gamepad_group.addSettingCard(self.xbox_key_special_attack_opt)

        self.xbox_key_ultimate_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='终结技', options_enum=XboxButtonEnum)
        self.xbox_key_ultimate_opt.value_changed.connect(self._on_xbox_key_ultimate_changed)
        gamepad_group.addSettingCard(self.xbox_key_ultimate_opt)

        self.xbox_key_interact_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='交互', options_enum=XboxButtonEnum)
        self.xbox_key_interact_opt.value_changed.connect(self._on_xbox_key_interact_changed)
        gamepad_group.addSettingCard(self.xbox_key_interact_opt)

        self.xbox_key_chain_left_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-左', options_enum=XboxButtonEnum)
        self.xbox_key_interact_opt.value_changed.connect(self._on_xbox_key_chain_left_changed)
        gamepad_group.addSettingCard(self.xbox_key_chain_left_opt)

        self.xbox_key_chain_right_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-右', options_enum=XboxButtonEnum)
        self.xbox_key_interact_opt.value_changed.connect(self._on_xbox_key_chain_right_changed)
        gamepad_group.addSettingCard(self.xbox_key_chain_right_opt)

        self.xbox_key_move_w_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-前', options_enum=XboxButtonEnum)
        self.xbox_key_move_w_opt.value_changed.connect(self._on_xbox_key_move_w_changed)
        gamepad_group.addSettingCard(self.xbox_key_move_w_opt)

        self.xbox_key_move_s_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-后', options_enum=XboxButtonEnum)
        self.xbox_key_move_s_opt.value_changed.connect(self._on_xbox_key_move_s_changed)
        gamepad_group.addSettingCard(self.xbox_key_move_s_opt)

        self.xbox_key_move_a_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-左', options_enum=XboxButtonEnum)
        self.xbox_key_move_a_opt.value_changed.connect(self._on_xbox_key_move_a_changed)
        gamepad_group.addSettingCard(self.xbox_key_move_a_opt)

        self.xbox_key_move_d_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-右', options_enum=XboxButtonEnum)
        self.xbox_key_move_d_opt.value_changed.connect(self._on_xbox_key_move_d_changed)
        gamepad_group.addSettingCard(self.xbox_key_move_d_opt)

        # ds4
        self.ds4_key_press_time_opt = TextSettingCard(icon=FluentIcon.GAME, title='单次按键持续时间(秒)',
                                                      content='自行调整，过小可能按键被吞，过大可能影响操作')
        self.ds4_key_press_time_opt.value_changed.connect(self._on_ds4_key_press_time_changed)
        gamepad_group.addSettingCard(self.ds4_key_press_time_opt)

        self.ds4_key_normal_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='普通攻击', options_enum=Ds4ButtonEnum)
        self.ds4_key_normal_attack_opt.value_changed.connect(self._on_ds4_key_normal_attack_changed)
        gamepad_group.addSettingCard(self.ds4_key_normal_attack_opt)

        self.ds4_key_dodge_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='闪避', options_enum=Ds4ButtonEnum)
        self.ds4_key_dodge_opt.value_changed.connect(self._on_ds4_key_dodge_changed)
        gamepad_group.addSettingCard(self.ds4_key_dodge_opt)

        self.ds4_key_switch_next_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-下一个', options_enum=Ds4ButtonEnum)
        self.ds4_key_switch_next_opt.value_changed.connect(self._on_ds4_key_switch_next_changed)
        gamepad_group.addSettingCard(self.ds4_key_switch_next_opt)

        self.ds4_key_switch_prev_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='角色切换-上一个', options_enum=Ds4ButtonEnum)
        self.ds4_key_switch_prev_opt.value_changed.connect(self._on_ds4_key_switch_prev_changed)
        gamepad_group.addSettingCard(self.ds4_key_switch_prev_opt)

        self.ds4_key_special_attack_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='特殊攻击', options_enum=Ds4ButtonEnum)
        self.ds4_key_special_attack_opt.value_changed.connect(self._on_ds4_key_special_attack_changed)
        gamepad_group.addSettingCard(self.ds4_key_special_attack_opt)

        self.ds4_key_ultimate_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='终结技', options_enum=Ds4ButtonEnum)
        self.ds4_key_ultimate_opt.value_changed.connect(self._on_ds4_key_ultimate_changed)
        gamepad_group.addSettingCard(self.ds4_key_ultimate_opt)

        self.ds4_key_interact_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='交互', options_enum=Ds4ButtonEnum)
        self.ds4_key_interact_opt.value_changed.connect(self._on_ds4_key_interact_changed)
        gamepad_group.addSettingCard(self.ds4_key_interact_opt)

        self.ds4_key_chain_left_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-左', options_enum=Ds4ButtonEnum)
        self.ds4_key_interact_opt.value_changed.connect(self._on_ds4_key_chain_left_changed)
        gamepad_group.addSettingCard(self.ds4_key_chain_left_opt)

        self.ds4_key_chain_right_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='连携技-右', options_enum=Ds4ButtonEnum)
        self.ds4_key_interact_opt.value_changed.connect(self._on_ds4_key_chain_right_changed)
        gamepad_group.addSettingCard(self.ds4_key_chain_right_opt)

        self.ds4_key_move_w_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-前', options_enum=Ds4ButtonEnum)
        self.ds4_key_move_w_opt.value_changed.connect(self._on_ds4_key_move_w_changed)
        gamepad_group.addSettingCard(self.ds4_key_move_w_opt)

        self.ds4_key_move_s_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-后', options_enum=Ds4ButtonEnum)
        self.ds4_key_move_s_opt.value_changed.connect(self._on_ds4_key_move_s_changed)
        gamepad_group.addSettingCard(self.ds4_key_move_s_opt)

        self.ds4_key_move_a_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-左', options_enum=Ds4ButtonEnum)
        self.ds4_key_move_a_opt.value_changed.connect(self._on_ds4_key_move_a_changed)
        gamepad_group.addSettingCard(self.ds4_key_move_a_opt)

        self.ds4_key_move_d_opt = ComboBoxSettingCard(icon=FluentIcon.GAME, title='移动-右', options_enum=Ds4ButtonEnum)
        self.ds4_key_move_d_opt.value_changed.connect(self._on_ds4_key_move_d_changed)
        gamepad_group.addSettingCard(self.ds4_key_move_d_opt)

        return gamepad_group

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        game_region = get_config_item_from_enum(GameRegionEnum, self.ctx.game_config.game_region)
        if game_region is not None:
            self.game_region_opt.setValue(game_region.value)

        self.key_normal_attack_opt.setValue(self.ctx.game_config.key_normal_attack)
        self.key_dodge_opt.setValue(self.ctx.game_config.key_dodge)
        self.key_switch_next_opt.setValue(self.ctx.game_config.key_switch_next)
        self.key_switch_prev_opt.setValue(self.ctx.game_config.key_switch_prev)
        self.key_special_attack_opt.setValue(self.ctx.game_config.key_special_attack)
        self.key_ultimate_opt.setValue(self.ctx.game_config.key_ultimate)
        self.key_interact_opt.setValue(self.ctx.game_config.key_interact)
        self.key_chain_left_opt.setValue(self.ctx.game_config.key_chain_left)
        self.key_chain_right_opt.setValue(self.ctx.game_config.key_chain_right)
        self.key_move_w_opt.setValue(self.ctx.game_config.key_move_w)
        self.key_move_s_opt.setValue(self.ctx.game_config.key_move_s)
        self.key_move_a_opt.setValue(self.ctx.game_config.key_move_a)
        self.key_move_d_opt.setValue(self.ctx.game_config.key_move_d)

        self._update_gamepad_part()

    def _update_gamepad_part(self) -> None:
        """
        手柄部分更新显示
        :return:
        """
        self.gamepad_type_opt.setValue(self.ctx.game_config.gamepad_type)

        is_xbox = self.ctx.game_config.gamepad_type == GamepadTypeEnum.XBOX.value.value

        self.xbox_key_press_time_opt.setValue(str(self.ctx.game_config.xbox_key_press_time))
        self.xbox_key_normal_attack_opt.setValue(self.ctx.game_config.xbox_key_normal_attack)
        self.xbox_key_dodge_opt.setValue(self.ctx.game_config.xbox_key_dodge)
        self.xbox_key_switch_next_opt.setValue(self.ctx.game_config.xbox_key_switch_next)
        self.xbox_key_switch_prev_opt.setValue(self.ctx.game_config.xbox_key_switch_prev)
        self.xbox_key_special_attack_opt.setValue(self.ctx.game_config.xbox_key_special_attack)
        self.xbox_key_ultimate_opt.setValue(self.ctx.game_config.xbox_key_ultimate)
        self.xbox_key_interact_opt.setValue(self.ctx.game_config.xbox_key_interact)
        self.xbox_key_chain_left_opt.setValue(self.ctx.game_config.xbox_key_chain_left)
        self.xbox_key_chain_right_opt.setValue(self.ctx.game_config.xbox_key_chain_right)
        self.xbox_key_move_w_opt.setValue(self.ctx.game_config.xbox_key_move_w)
        self.xbox_key_move_s_opt.setValue(self.ctx.game_config.xbox_key_move_s)
        self.xbox_key_move_a_opt.setValue(self.ctx.game_config.xbox_key_move_a)
        self.xbox_key_move_d_opt.setValue(self.ctx.game_config.xbox_key_move_d)

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

        is_ds4 = self.ctx.game_config.gamepad_type == GamepadTypeEnum.DS4.value.value

        self.ds4_key_press_time_opt.setValue(str(self.ctx.game_config.ds4_key_press_time))
        self.ds4_key_normal_attack_opt.setValue(self.ctx.game_config.ds4_key_normal_attack)
        self.ds4_key_dodge_opt.setValue(self.ctx.game_config.ds4_key_dodge)
        self.ds4_key_switch_next_opt.setValue(self.ctx.game_config.ds4_key_switch_next)
        self.ds4_key_switch_prev_opt.setValue(self.ctx.game_config.ds4_key_switch_prev)
        self.ds4_key_special_attack_opt.setValue(self.ctx.game_config.ds4_key_special_attack)
        self.ds4_key_ultimate_opt.setValue(self.ctx.game_config.ds4_key_ultimate)
        self.ds4_key_interact_opt.setValue(self.ctx.game_config.ds4_key_interact)
        self.ds4_key_chain_left_opt.setValue(self.ctx.game_config.ds4_key_chain_left)
        self.ds4_key_chain_right_opt.setValue(self.ctx.game_config.ds4_key_chain_right)
        self.ds4_key_move_w_opt.setValue(self.ctx.game_config.ds4_key_move_w)
        self.ds4_key_move_s_opt.setValue(self.ctx.game_config.ds4_key_move_s)
        self.ds4_key_move_a_opt.setValue(self.ctx.game_config.ds4_key_move_a)
        self.ds4_key_move_d_opt.setValue(self.ctx.game_config.ds4_key_move_d)

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

    def _on_game_region_changed(self, index, value):
        self.ctx.game_config.game_region = value
        self.ctx.init_by_config()

    def _on_key_normal_attack_changed(self, key: str) -> None:
        self.ctx.game_config.key_normal_attack = key

    def _on_key_dodge_changed(self, key: str) -> None:
        self.ctx.game_config.key_dodge = key

    def _on_key_switch_next_changed(self, key: str) -> None:
        self.ctx.game_config.key_switch_next = key

    def _on_key_switch_prev_changed(self, key: str) -> None:
        self.ctx.game_config.key_switch_prev = key

    def _on_key_special_attack_changed(self, key: str) -> None:
        self.ctx.game_config.key_special_attack = key

    def _on_key_ultimate_changed(self, key: str) -> None:
        self.ctx.game_config.key_ultimate = key

    def _on_key_interact_changed(self, key: str) -> None:
        self.ctx.game_config.key_interact = key

    def _on_key_chain_left_changed(self, key: str) -> None:
        self.ctx.game_config.key_chain_left = key

    def _on_key_chain_right_changed(self, key: str) -> None:
        self.ctx.game_config.key_chain_right = key

    def _on_key_move_w_changed(self, key: str) -> None:
        self.ctx.game_config.key_move_w = key

    def _on_key_move_s_changed(self, key: str) -> None:
        self.ctx.game_config.key_move_s = key

    def _on_key_move_a_changed(self, key: str) -> None:
        self.ctx.game_config.key_move_a = key

    def _on_key_move_d_changed(self, key: str) -> None:
        self.ctx.game_config.key_move_d = key

    def _on_gamepad_type_changed(self, idx: int, value: str) -> None:
        self.ctx.game_config.gamepad_type = value
        self._update_gamepad_part()

    def _on_xbox_key_press_time_changed(self, value: str) -> None:
        self.ctx.game_config.xbox_key_press_time = float(value)

    def _on_xbox_key_normal_attack_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_normal_attack = key

    def _on_xbox_key_dodge_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_dodge = key

    def _on_xbox_key_switch_next_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_switch_next = key

    def _on_xbox_key_switch_prev_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_switch_prev = key

    def _on_xbox_key_special_attack_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_special_attack = key

    def _on_xbox_key_ultimate_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_ultimate = key

    def _on_xbox_key_interact_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.xbox_key_interact = key

    def _on_xbox_key_chain_left_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_chain_left = key

    def _on_xbox_key_chain_right_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_chain_right = key

    def _on_xbox_key_move_w_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_move_w = key

    def _on_xbox_key_move_s_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_move_s = key

    def _on_xbox_key_move_a_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_move_a = key

    def _on_xbox_key_move_d_changed(self, key: str) -> None:
        self.ctx.game_config.xbox_key_move_d = key

    def _on_ds4_key_press_time_changed(self, value: str) -> None:
        self.ctx.game_config.ds4_key_press_time = float(value)

    def _on_ds4_key_normal_attack_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_normal_attack = key

    def _on_ds4_key_dodge_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_dodge = key

    def _on_ds4_key_switch_next_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_switch_next = key

    def _on_ds4_key_switch_prev_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_switch_prev = key

    def _on_ds4_key_special_attack_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_special_attack = key

    def _on_ds4_key_ultimate_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_ultimate = key

    def _on_ds4_key_interact_changed(self, idx: int, key: str) -> None:
        self.ctx.game_config.ds4_key_interact = key

    def _on_ds4_key_chain_left_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_chain_left = key

    def _on_ds4_key_chain_right_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_chain_right = key

    def _on_ds4_key_move_w_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_move_w = key

    def _on_ds4_key_move_s_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_move_s = key

    def _on_ds4_key_move_a_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_move_a = key

    def _on_ds4_key_move_d_changed(self, key: str) -> None:
        self.ctx.game_config.ds4_key_move_d = key
