from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon

from one_dragon.base.config.push_config import NotifyMethodEnum, NotifyCard
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.setting_card.text_setting_card import TextSettingCard


class SettingPushInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):

        VerticalScrollInterface.__init__(
            self,
            object_name='setting_push_interface',
            content_widget=None, parent=parent,
            nav_text_cn='通知设置'
        )
        self.ctx: OneDragonContext = ctx

    def get_content_widget(self) -> QWidget:
        content_widget = Column()

        self.custom_push_title = TextSettingCard(
            icon=FluentIcon.MESSAGE,
            title='自定义通知标题',
            input_placeholder='一条龙运行通知'
        )
        content_widget.add_widget(self.custom_push_title)

        self.send_image_opt = SwitchSettingCard(icon=FluentIcon.PHOTO, title='通知中附带图片')
        content_widget.add_widget(self.send_image_opt)

        # 通知方式选择
        self.notification_method_opt = ComboBoxSettingCard(
            icon=FluentIcon.MESSAGE,
            title='通知方式',
            options_enum=NotifyMethodEnum
        )
        self.notification_method_opt.value_changed.connect(self._update_notification_ui)
        content_widget.add_widget(self.notification_method_opt)

        self.cards = {} 
        for method, configs in NotifyCard.configs.items():
            method_cards = []
            
            for config in configs:
                # 动态生成变量名（如：tg_bot_token_card）
                var_name = f"{method}_{config['var_suffix']}_notify_card".lower()
                title=config["title"]
                # 创建卡片实例
                card = TextSettingCard(
                    icon=config["icon"],
                    title=title,
                    input_max_width=320,
                    input_placeholder=config["placeholder"]
                )
                
                # 设置关键属性
                card.setObjectName(var_name.lower())  # 设置唯一标识
                card.setVisible(False)        # 初始状态隐藏
                
                # 将卡片存入实例变量
                setattr(self, var_name, card)
                method_cards.append(card)
            
            # 按方法分组存储
            self.cards[method] = method_cards
        
        # 将卡片添加到界面布局（根据实际布局调整）
        for cards in self.cards.values():
            for card in cards:
                content_widget.add_widget(card)
            
        content_widget.add_stretch(1)

        return content_widget

    def _update_notification_ui(self):
        """根据选择的通知方式更新界面"""
        method = self.notification_method_opt.combo_box.currentData()
        # 隐藏所有配置项
        for widget in self.findChildren(TextSettingCard):
            if widget.objectName().endswith("_notify_card"):
                widget.setVisible(False)

        prefix = f"{method.lower()}_"
        for widget in self.findChildren(TextSettingCard):
            if widget.objectName().startswith(prefix):
                widget.setVisible(True)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.custom_push_title.init_with_adapter(self.ctx.push_config.get_prop_adapter('custom_push_title'))
        self.send_image_opt.init_with_adapter(self.ctx.push_config.get_prop_adapter('send_image'))

        # 动态初始化所有通知卡片
        for method_group, configs in NotifyCard.configs.items():
            for config in configs:
                var_suffix = config["var_suffix"]
                var_name = f"{method_group.lower()}_{var_suffix.lower()}_notify_card"
                config_key = f"{method_group.lower()}_{var_suffix.lower()}"
                
                card = getattr(self, var_name, None)
                if card:
                    card.init_with_adapter(self.ctx.push_config.get_prop_adapter(config_key))
                else:
                    print(f"未找到卡片: {var_name}")
    
        # 初始更新界面状态
        self._update_notification_ui()
