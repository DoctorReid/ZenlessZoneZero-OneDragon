from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class BasicNotifyConfig(YamlConfig):

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
        for app in self.app_list.items():
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
            setattr(BasicNotifyConfig, prop_name, prop)
