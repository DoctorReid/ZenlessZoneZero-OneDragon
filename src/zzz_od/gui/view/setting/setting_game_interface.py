from qfluentwidgets import SettingCardGroup, FluentIcon

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.key_setting_card import KeySettingCard
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext


class SettingGameInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        content_widget = ColumnWidget()

        key_group = SettingCardGroup(gt('游戏按键', 'ui'))
        content_widget.add_widget(key_group)

        self.attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='攻击')
        self.attack_opt.value_changed.connect(self._on_key_attack_changed)
        key_group.addSettingCard(self.attack_opt)

        self.dodge_opt = KeySettingCard(icon=FluentIcon.GAME, title='闪避')
        self.dodge_opt.value_changed.connect(self._on_key_dodge_changed)
        key_group.addSettingCard(self.dodge_opt)

        self.switch_next_opt = KeySettingCard(icon=FluentIcon.GAME, title='换人-下一个')
        self.switch_next_opt.value_changed.connect(self._on_key_switch_next_changed)
        key_group.addSettingCard(self.switch_next_opt)

        self.switch_prev_opt = KeySettingCard(icon=FluentIcon.GAME, title='换人-上一个')
        self.switch_prev_opt.value_changed.connect(self._on_key_switch_prev_changed)
        key_group.addSettingCard(self.switch_prev_opt)

        self.key_technique_opt = KeySettingCard(icon=FluentIcon.GAME, title='核心技')
        self.key_technique_opt.value_changed.connect(self._on_key_technique_changed)
        key_group.addSettingCard(self.key_technique_opt)

        self.key_ultimate_opt = KeySettingCard(icon=FluentIcon.GAME, title='爆发技')
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

    def init_on_shown(self) -> None:
        self.attack_opt.setValue(self.ctx.game_config.key_attack)
        self.dodge_opt.setValue(self.ctx.game_config.key_dodge)
        self.switch_next_opt.setValue(self.ctx.game_config.key_change_next)
        self.switch_prev_opt.setValue(self.ctx.game_config.key_change_prev)
        self.key_technique_opt.setValue(self.ctx.game_config.key_technique)
        self.key_ultimate_opt.setValue(self.ctx.game_config.key_ultimate)
        self.key_interact_opt.setValue(self.ctx.game_config.key_interact)

    def _on_key_attack_changed(self, key: str) -> None:
        self.ctx.game_config.key_attack = key

    def _on_key_dodge_changed(self, key: str) -> None:
        self.ctx.game_config.key_attack = key

    def _on_key_switch_next_changed(self, key: str) -> None:
        self.ctx.game_config.key_change_next = key

    def _on_key_switch_prev_changed(self, key: str) -> None:
        self.ctx.game_config.key_change_prev = key

    def _on_key_technique_changed(self, key: str) -> None:
        self.ctx.game_config.key_technique = key

    def _on_key_ultimate_changed(self, key: str) -> None:
        self.ctx.game_config.key_ultimate = key

    def _on_key_interact_changed(self, key: str) -> None:
        self.ctx.game_config.key_interact = key
