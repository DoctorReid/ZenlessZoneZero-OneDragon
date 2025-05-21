import os
from enum import Enum
from typing import Optional
from qfluentwidgets import FluentIcon

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.utils import os_utils


class NotifyMethodEnum(Enum):

    SMTP = ConfigItem('邮件', 'SMTP')
    WEBHOOK = ConfigItem('Webhook', 'WEBHOOK')
    ONEBOT = ConfigItem('OneBot', 'ONEBOT')
    CHRONOCAT = ConfigItem('Chronocat', 'CHRONOCAT')
    QYWX = ConfigItem('企业微信', 'QYWX')
    DD_BOT = ConfigItem('钉钉机器人', 'DD_BOT')
    FS =  ConfigItem('飞书机器人', 'FS')
    DISCORD = ConfigItem('Discord', 'DISCORD')
    TELEGRAM = ConfigItem('Telegram', 'TG')
    BARK = ConfigItem('Bark', 'BARK')
    SERVERCHAN = ConfigItem('Server 酱', 'SERVERCHAN')
    NTFY = ConfigItem('ntfy', 'NTFY')
    DEER = ConfigItem('PushDeer', 'DEER')
    GOTIFY = ConfigItem('GOTIFY', 'GOTIFY')
    IGOT = ConfigItem('iGot', 'IGOT')
    CHAT = ConfigItem('Synology Chat', 'CHAT')
    PUSH_PLUS = ConfigItem('PushPlus', 'PUSH_PLUS')
    WE_PLUS_BOT = ConfigItem('微加机器人', 'WE_PLUS_BOT')
    QMSG = ConfigItem('Qmsg 酱', 'QMSG')
    AIBOTK = ConfigItem('智能微秘书', 'AIBOTK')
    PUSHME = ConfigItem('PushMe', 'PUSHME')
    WXPUSHER = ConfigItem('WxPusher', 'WXPUSHER')

class PushConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(self, 'push', instance_idx=instance_idx)
        self._generate_dynamic_properties()

    @property
    def custom_push_title(self) -> str:
        return self.get('custom_push_title', '一条龙运行通知')

    @custom_push_title.setter
    def custom_push_title(self, new_value: str) -> None:
        self.update('custom_push_title', new_value)

    @property
    def send_image(self) -> bool:
        return self.get('send_image', True)

    @send_image.setter
    def send_image(self, new_value: bool) -> None:
        self.update('send_image', new_value)

    def _generate_dynamic_properties(self):
        # 遍历所有配置组
        for group_name, items in PushCard.get_configs().items():
            group_lower = group_name.lower()
            # 遍历组内的每个配置项
            for item in items:
                var_suffix = item["var_suffix"]
                var_suffix_lower = var_suffix.lower()
                prop_name = f"{group_lower}_{var_suffix_lower}"

                # 定义getter和setter，使用闭包捕获当前的prop_name
                def create_getter(name: str):
                    def getter(self) -> float:
                        return self.get(name, None)
                    return getter

                def create_setter(name: str):
                    def setter(self, new_value: float) -> None:
                        self.update(name, new_value)
                    return setter

                # 创建property并添加到类
                prop = property(
                    create_getter(prop_name),
                    create_setter(prop_name)
                )
                setattr(PushConfig, prop_name, prop)

class PushCard:
    _configs = None
    _yaml_path = os.path.join(
                os_utils.get_path_under_work_dir('src', 'one_dragon', 'base', 'config'),
                'push_cards.yml'
            )

    @classmethod
    def load_configs(cls):
        if cls._configs is None:
            if os.path.exists(cls._yaml_path):
                raw = YamlOperator(cls._yaml_path).data or {}
                # icon 字段转为 FluentIcon
                for group, items in raw.items():
                    for item in items:
                        icon_name = item.get("icon")
                        if icon_name and hasattr(FluentIcon, icon_name):
                            item["icon"] = getattr(FluentIcon, icon_name)
                cls._configs = raw
            else:
                cls._configs = {}
        return cls._configs

    @classmethod
    def get_configs(cls):
        return cls.load_configs()

class EmailServiceConfig:
    _services = None
    _yaml_path =os.path.join(
                os_utils.get_path_under_work_dir('src', 'one_dragon', 'base', 'config'),
                'push_email_services.yml'
            )

    @classmethod
    def load_services(cls):
        if cls._services is None:
            if os.path.exists(cls._yaml_path):
                cls._services = YamlOperator(cls._yaml_path).data or {}
            else:
                cls._services = {}
        return cls._services

    @classmethod
    def get_configs(cls, keyword: str):
        """
        根据关键词、别名、域名查找邮箱服务配置。
        :param keyword: 用户输入的邮箱服务关键字（如 qq/gmail/163/域名等）
        :return: 匹配到的邮箱服务配置 dict 或 None
        """
        services = cls.load_services()
        key = keyword.strip().lower()
        for service_name, config in services.items():
            # 关键词匹配
            if key == service_name.lower():
                return config
            # 匹配别名
            if "aliases" in config and key in [alias.lower() for alias in config["aliases"]]:
                return config
            # 匹配域名
            if "domains" in config and key in [domain.lower() for domain in config["domains"]]:
                return config
        return None
