from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from qfluentwidgets import FluentIcon


class NotifyAppList():
    app_list = {
        'redemption_code': '兑换码',
        'random_play': '影像店营业',
        'scratch_card': '刮刮卡',
        'charge_plan': '体力刷本',
        'coffee': '咖啡店',
        'notorious_hunt': '恶名狩猎',
        'engagement_reward': '活跃度奖励',
        'hollow_zero': '枯萎之都',
        'lost_void': '迷失之地',
        'shiyu_defense': '式舆防卫战',
        'city_fund': '丽都城募',
        'ridu_weekly': '丽都周纪(领奖励)',
        'email': '邮件',
        'drive_disc_dismantle': '驱动盘分解',
        'life_on_line': '真拿命验收'
    }

class NotifyConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(self, 'notify', instance_idx=instance_idx)
        self._generate_dynamic_properties()
    
    @property
    def enable_notify(self) -> bool:
        return self.get('enable_notify', True)
    
    @enable_notify.setter
    def enable_notify(self, new_value: bool) -> None:
        self.update('enable_notify', new_value)

    def _generate_dynamic_properties(self):
        for app in NotifyAppList.app_list.items():
            prop_name = app[0]
            def create_getter(name: str):
                def getter(self) -> bool:
                    return self.get(name, True)
                return getter
            
            def create_setter(name: str):
                def setter(self, new_value: bool) -> None:
                    self.update(name, new_value)
                return setter
            
            # 创建property并添加到类
            prop = property(
                create_getter(prop_name),
                create_setter(prop_name)
            )
            setattr(NotifyConfig, prop_name, prop)
