from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon

from one_dragon.base.config.push_config import NotifyMethodEnum, PushCard, EmailServiceConfig
from one_dragon.base.notify.push import Push
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon_qt.widgets.setting_card.combo_box_setting_card import ComboBoxSettingCard
from one_dragon_qt.widgets.setting_card.push_setting_card import PushSettingCard
from one_dragon_qt.widgets.vertical_scroll_interface import VerticalScrollInterface
from one_dragon_qt.widgets.column import Column
from one_dragon_qt.widgets.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon_qt.widgets.setting_card.text_setting_card import TextSettingCard
from one_dragon_qt.widgets.setting_card.editable_combo_box_setting_card import EditableComboBoxSettingCard


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

        self.test_btn = PushSettingCard(icon=FluentIcon.SEND, title='测试通知', text='发送测试消息')
        self.test_btn.clicked.connect(self._send_test_message)
        content_widget.add_widget(self.test_btn)

        # 通知方式选择
        self.notification_method_opt = ComboBoxSettingCard(
            icon=FluentIcon.MESSAGE,
            title='通知方式',
            options_enum=NotifyMethodEnum
        )
        self.notification_method_opt.value_changed.connect(self._update_notification_ui)
        content_widget.add_widget(self.notification_method_opt)

        # 新增：邮箱服务下拉栏（仅在SMTP方式下显示）
        email_services = EmailServiceConfig.load_services()
        class SimpleOption:
            def __init__(self, text):
                self.ui_text = text
                self.value = text
                self.desc = ""  # 必须有desc属性，哪怕为空字符串
        service_options = [SimpleOption(name) for name in email_services.keys()]
        self.email_service_combo = EditableComboBoxSettingCard(
            icon=FluentIcon.MESSAGE,
            title='邮箱服务类型',
            options_list=service_options
        )
        self.email_service_combo.combo_box.setFixedWidth(320)
        self.email_service_combo.value_changed.connect(lambda idx, val: self._on_email_service_selected(val))
        self.email_service_combo.setVisible(False)  # 默认隐藏，SMTP方式时显示
        content_widget.add_widget(self.email_service_combo)

        self.cards = {} 
        for method, configs in PushCard.get_configs().items():
            method_lower = method.lower()
            method_cards = []
            for config in configs:
                var_name = f"{method_lower}_{config['var_suffix'].lower()}_push_card"
                title = config["title"]
                card = TextSettingCard(
                    icon=config["icon"],
                    title=title,
                    input_max_width=320,
                    input_placeholder=config["placeholder"]
                )
                card.setObjectName(var_name)  # 统一小写
                card.setVisible(False)
                setattr(self, var_name, card)
                method_cards.append(card)
            self.cards[method_lower] = method_cards
        
        # 将卡片添加到界面布局（根据实际布局调整）
        for cards in self.cards.values():
            for card in cards:
                content_widget.add_widget(card)
            
        content_widget.add_stretch(1)

        return content_widget

    def _send_test_message(self):
        """发送测试消息"""
        pusher = Push(self.ctx)
        pusher.send("这是一条测试消息", None, self.notification_method_opt.getValue())

    def _on_email_service_selected(self, text):
        config = EmailServiceConfig.get_configs(str(text))
        if config:
            # 自动填充SMTP相关卡片
            smtp_server = config["host"]
            smtp_port = config.get("port", 465)
            smtp_ssl = str(config.get("secure", True)).lower() if "secure" in config else "true"
            # 找到对应的TextSettingCard并赋值
            if hasattr(self, "smtp_server_push_card"):
                self.smtp_server_push_card.setValue(f"{smtp_server}:{smtp_port}")
            if hasattr(self, "smtp_ssl_push_card"):
                self.smtp_ssl_push_card.setValue(smtp_ssl)

    def _update_notification_ui(self):
        """根据选择的通知方式更新界面"""
        method = self.notification_method_opt.getValue()
        # 隐藏所有配置项
        for widget in self.findChildren(TextSettingCard):
            if widget.objectName().endswith("_push_card"):
                widget.setVisible(False)

        # 只在SMTP方式下显示邮箱服务下拉栏
        if method == "SMTP":
            self.email_service_combo.setVisible(True)
        else:
            self.email_service_combo.setVisible(False)

        prefix = f"{method.lower()}_"
        for widget in self.findChildren(TextSettingCard):
            if widget.objectName().startswith(prefix):
                widget.setVisible(True)

    def on_interface_shown(self) -> None:
        VerticalScrollInterface.on_interface_shown(self)

        self.custom_push_title.init_with_adapter(self.ctx.push_config.get_prop_adapter('custom_push_title'))
        self.send_image_opt.init_with_adapter(self.ctx.push_config.get_prop_adapter('send_image'))

        # 动态初始化所有通知卡片
        for method_group, configs in PushCard.get_configs().items():
            method_group_lower = method_group.lower()
            for config in configs:
                var_suffix = config["var_suffix"].lower()
                var_name = f"{method_group_lower}_{var_suffix}_push_card"
                config_key = f"{method_group_lower}_{var_suffix}"
                
                card = getattr(self, var_name, None)
                if card:
                    card.init_with_adapter(self.ctx.push_config.get_prop_adapter(config_key))
                else:
                    print(f"未找到卡片: {var_name}")
    
        # 初始更新界面状态
        self._update_notification_ui()
