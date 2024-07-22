from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.base.config.config_item import get_config_item_from_enum
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.utils.i18_utils import gt
from zzz_od.config.game_config import GameRegionEnum
from zzz_od.context.zzz_context import ZContext


class SettingGameInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        content_widget = ColumnWidget()

        basic_group = SettingCardGroup(gt('游戏基础', 'ui'))
        content_widget.add_widget(basic_group)

        self.game_region_opt = ComboBoxSettingCard(icon=FluentIcon.HOME, title='游戏区服', options_enum=GameRegionEnum)
        self.game_region_opt.value_changed.connect(self._on_game_region_changed)
        basic_group.addSettingCard(self.game_region_opt)

        key_group = SettingCardGroup(gt('游戏按键', 'ui'))
        content_widget.add_widget(key_group)

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

        content_widget.add_stretch(1)

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            object_name='setting_game_interface',
            content_widget=content_widget, parent=parent,
            nav_text_cn='游戏设置'
        )

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
