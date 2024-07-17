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

        self.key_normal_attack_opt = KeySettingCard(icon=FluentIcon.GAME, title='普通攻击')
        self.key_normal_attack_opt.value_changed.connect(self._on_key_normal_attack_changed)
        key_group.addSettingCard(self.key_normal_attack_opt)

        self.dodge_opt = KeySettingCard(icon=FluentIcon.GAME, title='闪避')
        self.dodge_opt.value_changed.connect(self._on_key_dodge_changed)
        key_group.addSettingCard(self.dodge_opt)

        self.switch_next_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-下一个')
        self.switch_next_opt.value_changed.connect(self._on_key_switch_next_changed)
        key_group.addSettingCard(self.switch_next_opt)

        self.switch_prev_opt = KeySettingCard(icon=FluentIcon.GAME, title='角色切换-上一个')
        self.switch_prev_opt.value_changed.connect(self._on_key_switch_prev_changed)
        key_group.addSettingCard(self.switch_prev_opt)

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
        self.key_normal_attack_opt.setValue(self.ctx.game_config.key_normal_attack)
        self.dodge_opt.setValue(self.ctx.game_config.key_dodge)
        self.switch_next_opt.setValue(self.ctx.game_config.key_switch_next)
        self.switch_prev_opt.setValue(self.ctx.game_config.key_switch_prev)
        self.key_special_attack_opt.setValue(self.ctx.game_config.key_special_attack)
        self.key_ultimate_opt.setValue(self.ctx.game_config.key_ultimate)
        self.key_interact_opt.setValue(self.ctx.game_config.key_interact)

    def _on_key_normal_attack_changed(self, key: str) -> None:
        self.ctx.game_config.key_attack = key

    def _on_key_dodge_changed(self, key: str) -> None:
        self.ctx.game_config.key_attack = key

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
