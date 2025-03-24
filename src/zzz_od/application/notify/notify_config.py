from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from qfluentwidgets import FluentIcon


class NotifyMethodEnum(Enum):

    DISABLED = ConfigItem(label='禁用',value='DISABLED')
    
    BARK = ConfigItem('BARK')
    DD_BOT = ConfigItem(label='钉钉机器人',value='DD_BOT')
    FS =  ConfigItem(label='飞书机器人',value='FS')
    GOBOT = ConfigItem('GoBot')
    GOTIFY = ConfigItem('GOTIFY')
    IGOT = ConfigItem('IGOT')
    ServerChan = ConfigItem(label='Server酱',value='PUSH_KEY')
    DEER = ConfigItem(label='PushDeer',value='DEER')
    CHAT = ConfigItem(label='synology chat',value='CHAT')
    PUSH_PLUS = ConfigItem(label='PushPlus',value='PUSH_PLUS')
    WE_PLUS_BOT = ConfigItem(label='微加机器人',value='WE_PLUS_BOT')
    QMSG = ConfigItem(label='QMSG酱',value='QMSG')
    QYWX = ConfigItem(label='企业微信',value='QYWX')
    Telegram = ConfigItem(label='Telegram',value='TG')
    AIBOTK = ConfigItem(label='智能微秘书',value='AIBOTK')
    SMTP = ConfigItem(label='邮件',value='SMTP')
    PushMe = ConfigItem('PushMe')
    CHRONOCAT = ConfigItem('CHRONOCAT')
    WEBHOOK = ConfigItem('WEBHOOK')
    NTFY = ConfigItem('NTFY')
    WXPUSHER = ConfigItem('WXPUSHER')



class NotifyConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(self, 'notify', instance_idx=instance_idx)
        self._generate_dynamic_properties()
    
    
    @property
    def notify_method(self) -> str:
        return self.get('notify_method', NotifyMethodEnum.DISABLED)

    @notify_method.setter
    def notify_method(self, new_value: str) -> None:
        self.update('notify_method', new_value)

    def _generate_dynamic_properties(self):
        # 遍历所有配置组
        for group_name, items in NotifyCard.configs.items():
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
                setattr(NotifyConfig, prop_name, prop)

class NotifyCard():
    configs = {
    # BARK 相关配置
    "BARK": [
        {
            "var_suffix": "PUSH", 
            "title": "设备码",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入bark IP 或设备码"
        },
        {
            "var_suffix": "ARCHIVE",
            "title": "推送是否存档",
            "icon": FluentIcon.PEOPLE,
            "placeholder": ""
        },
        {
            "var_suffix": "GROUP",
            "title": "推送分组",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        },
        {
            "var_suffix": "SOUND",
            "title": "推送声音",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        },
        {
            "var_suffix": "ICON",
            "title": "推送图标",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        },
        {
            "var_suffix": "LEVEL",
            "title": "推送时效性",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        },
        {
            "var_suffix": "URL",
            "title": "推送跳转URL",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        }
    ],
    # 钉钉机器人相关配置
    "DD_BOT": [
        {
            "var_suffix": "SECRET'",
            "title": "SECRET",
            "icon": FluentIcon.CERTIFICATE,
            "placeholder": "请输入钉钉机器人的SECRET密钥"
        },
        {
            "var_suffix": "TOKEN",
            "title": "TOKEN",
            "icon": FluentIcon.LINK,
            "placeholder": "请输入钉钉机器人的TOKEN密钥"
        }
    ],
    # 飞书机器人 相关配置
    "FS": [
        {
            "var_suffix": "KEY",
            "title": "密钥",
            "icon": FluentIcon.CERTIFICATE,
            "placeholder": "请输入飞书机器人的密钥"
        }
    ],
    # GOTIFY 相关配置
    "GOTIFY": [
        {
            "var_suffix": "URL", 
            "title": "gotify地址",
            "icon": FluentIcon.CLOUD,
            "placeholder": "请输入gotify地址,如https://push.example.de:8080"
        },
        {
            "var_suffix": "TOKEN",
            "title": "TOKEN",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "gotify的消息应用token"
        },
        {
            "var_suffix": "PRIORITY",
            "title": "消息优先级",
            "icon": FluentIcon.CLOUD,
            "placeholder": "默认为0"
        }
    ],
    # IGOT 相关配置
    "IGOT": [
        {
            "var_suffix": "PUSH_KEY", 
            "title": "PUSH_KEY",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入iGot 聚合推送的 IGOT_PUSH_KEY"
        }
    ],
    # ServerChan 相关配置
    "PUSH": [
        {
            "var_suffix": "KEY",
            "title": "PUSH_KEY",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入ServerChan的PUSH_KEY"
        }
    ],
    # PushDeer 相关配置
    "DEER": [
        {
            "var_suffix": "KEY", 
            "title": "KEY",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入PushDeer 的 PUSHDEER_KEY"
        },
        {
            "var_suffix": "URL",
            "title": "推送URL",
            "icon": FluentIcon.CLOUD,
            "placeholder": "请输入PushDeer 的 PUSHDEER_URL"
        }
    ],
    # synology chat 相关配置
    "CHAT": [
        {
            "var_suffix": "URL", 
            "title": "synology chat url",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入synology chat的url"
        },
        {
            "var_suffix": "TOKEN",
            "title": "synology chat token",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入synology chat的token"
        }
    ],
    # PUSH_PLUS 相关配置
    "PUSH_PLUS": [
        {
            "var_suffix": "TOKEN", 
            "title": "用户令牌",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入用户令牌"
        },
        {
            "var_suffix": "USER",
            "title": "群组编码",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入群组编码"
        },
        {
            "var_suffix": "TEMPLATE",
            "title": "发送模板",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选：html,txt,json,markdown,cloudMonitor,jenkins,route"
        },
        {
            "var_suffix": "CHANNEL",
            "title": "发送渠道",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选：wechat,webhook,cp,mail,sms"
        },
        {
            "var_suffix": "WEBHOOK",
            "title": "webhook编码",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可在pushplus公众号上扩展配置出更多渠道"
        },
        {
            "var_suffix": "CALLBACKURL",
            "title": "发送结果回调地址",
            "icon": FluentIcon.CLOUD,
            "placeholder": "会把推送最终结果通知到这个地址上"
        },
        {
            "var_suffix": "TO",
            "title": "好友令牌",
            "icon": FluentIcon.CLOUD,
            "placeholder": "微信公众号渠道填写好友令牌，企业微信渠道填写企业微信用户id"
        }
    ],
    # 微加机器人 相关配置
    "WE_PLUS_BOT": [
        {
            "var_suffix": "TOKEN", 
            "title": "用户令牌",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入用户令牌"
        },
        {
            "var_suffix": "RECEIVER",
            "title": "消息接收者",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入消息接收者"
        },
        {
            "var_suffix": "VERSION",
            "title": "调用版本",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选"
        }
    ],
    # QMSG 相关配置
    "QMSG": [
        {
            "var_suffix": "KEY", 
            "title": "KEY",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入qmsg 酱的 QMSG_KEY"
        },
        {
            "var_suffix": "TYPE",
            "title": "TYPE",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入qmsg 酱的 QMSG_TYPE"
        }
    ],
    # 企业微信 相关配置
    "QYWX": [
        {
            "var_suffix": "ORIGIN", 
            "title": "企业微信代理地址",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "选一项填即可"
        },
        {
            "var_suffix": "AM",
            "title": "企业微信应用",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "选一项填即可"
        },
        {
            "var_suffix": "KEY",
            "title": "企业微信机器人",
            "icon": FluentIcon.CLOUD,
            "placeholder": "选一项填即可"
        }
    ],
    # TG_BOT 相关配置
    "TG": [
        {
            "var_suffix": "BOT_TOKEN", 
            "title": "BOT_TOKEN",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入tg 机器人的 TG_BOT_TOKEN，例：1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ"
        },
        {
            "var_suffix": "USER_ID",
            "title": "USER_ID",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入用户ID，例：1434078534"
        },
        {
            "var_suffix": "PROXY_HOST",
            "title": "PROXY_HOST",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选，例：127.0.0.1"
        },
        {
            "var_suffix": "PROXY_PORT",
            "title": "PROXY_PORT",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选，例：1080"
        },
        {
            "var_suffix": "PROXY_AUTH",
            "title": "PROXY_AUTH",
            "icon": FluentIcon.CLOUD,
            "placeholder": "代理认证参数"
        },
        {
            "var_suffix": "API_HOST",
            "title": "API_HOST",
            "icon": FluentIcon.CLOUD,
            "placeholder": "可选"
        }
    ],
    # 智能微秘书 相关配置
    "AIBOTK": [
        {
            "var_suffix": "KEY", 
            "title": "apikey",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入个人中心的apikey 文档地址：http://wechat.aibotk.com/docs/about"
        },
        {
            "var_suffix": "TYPE",
            "title": "目标类型",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入room 或 contact"
        },
        {
            "var_suffix": "NAME",
            "title": "目标名称",
            "icon": FluentIcon.CLOUD,
            "placeholder": "发送群名 或者好友昵称和type要对应好"
        }
    ],
    # SMTP 相关配置
    "SMTP": [
        {
            "var_suffix": "SERVER", 
            "title": "邮件服务器",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入SMTP 发送邮件服务器，形如 smtp.exmail.qq.com:465"
        },
        {
            "var_suffix": "SSL",
            "title": "是否使用 SSL",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "填写 true 或 false"
        },
        {
            "var_suffix": "EMAIL",
            "title": "邮箱",
            "icon": FluentIcon.CLOUD,
            "placeholder": "SMTP 收发件邮箱，通知将会由自己发给自己"
        },
        {
            "var_suffix": "PASSWORD",
            "title": "登录密码",
            "icon": FluentIcon.CLOUD,
            "placeholder": "SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定"
        },
        {
            "var_suffix": "NAME",
            "title": "收发件人",
            "icon": FluentIcon.CLOUD,
            "placeholder": "发件人名称，可随意填写"
        }
    ],
    # PUSHME 相关配置
    "PUSHME": [
        {
            "var_suffix": "KEY", 
            "title": "KEY",
            "icon": FluentIcon.MESSAGE,
            "placeholder": ""
        },
        {
            "var_suffix": "URL",
            "title": "URL",
            "icon": FluentIcon.PEOPLE,
            "placeholder": ""
        }
    ],
    # CHRONOCAT 相关配置
    "CHRONOCAT": [
        {
            "var_suffix": "QQ", 
            "title": "QQ",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入接受消息的QQ号"
        },
        {
            "var_suffix": "TOKEN",
            "title": "TOKEN",
            "icon": FluentIcon.PEOPLE,
            "placeholder": ""
        },
        {
            "var_suffix": "URL",
            "title": "URL",
            "icon": FluentIcon.CLOUD,
            "placeholder": ""
        }
    ],
    # WEBHOOK 相关配置
    "WEBHOOK": [
        {
            "var_suffix": "URL", 
            "title": "URL",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "自定义通知 请求地址"
        },
        {
            "var_suffix": "BODY",
            "title": "BODY",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "自定义通知 请求体"
        },
        {
            "var_suffix": "HEADERS",
            "title": "HEADERS",
            "icon": FluentIcon.CLOUD,
            "placeholder": "自定义通知 请求头"
        },
        {
            "var_suffix": "METHOD",
            "title": "METHOD",
            "icon": FluentIcon.CLOUD,
            "placeholder": "自定义通知 请求方法"
        },
        {
            "var_suffix": "CONTENT_TYPE",
            "title": "CONTENT_TYPE",
            "icon": FluentIcon.CLOUD,
            "placeholder": "自定义通知 content-type"
        }
    ],
    # NTFY 相关配置
    "NTFY": [
        {
            "var_suffix": "URL", 
            "title": "URL",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入ntfy地址,如https://ntfy.sh"
        },
        {
            "var_suffix": "TOPIC",
            "title": "TOPIC",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "ntfy的消息应用topic"
        },
        {
            "var_suffix": "PRIORITY",
            "title": "PRIORITY",
            "icon": FluentIcon.CLOUD,
            "placeholder": "推送消息优先级,默认为3"
        }
    ],
    # WXPUSHER 相关配置
    "WXPUSHER": [
        {
            "var_suffix": "APP_TOKEN", 
            "title": "APP_TOKEN",
            "icon": FluentIcon.MESSAGE,
            "placeholder": "请输入appToken，官方文档: https://wxpusher.zjiecode.com/docs/ 管理后台: https://wxpusher.zjiecode.com/admin/"
        },
        {
            "var_suffix": "TOPIC_IDS",
            "title": "TOPIC_IDS",
            "icon": FluentIcon.PEOPLE,
            "placeholder": "请输入主题ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行"
        },
        {
            "var_suffix": "UIDS",
            "title": "UIDS",
            "icon": FluentIcon.CLOUD,
            "placeholder": "用户ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行"
        }
    ],
}