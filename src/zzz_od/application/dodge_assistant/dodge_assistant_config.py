import os
from typing import List

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import os_utils


class DodgeAssistantConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'dodge_assistant', instance_idx=instance_idx)

    @property
    def dodge_way(self) -> str:
        return self.get('dodge_way', 'dodge')

    @dodge_way.setter
    def dodge_way(self, new_value: str) -> None:
        self.update('dodge_way', new_value)

    @property
    def use_gpu(self) -> bool:
        return self.get('use_gpu', True)

    @use_gpu.setter
    def use_gpu(self, new_value: bool) -> None:
        self.update('use_gpu', new_value)

    @property
    def screenshot_interval(self) -> float:
        return self.get('screenshot_interval', 0.02)

    @screenshot_interval.setter
    def screenshot_interval(self, new_value: float) -> None:
        self.update('screenshot_interval', new_value)


def get_dodge_op_config_list() -> List[ConfigItem]:
    """
    获取用于配置页面显示的指令列表
    :return:
    """
    op_list: List[ConditionalOperator] = get_all_dodge_op()
    return [ConfigItem(label=op.name, value=op.module_name)
            for op in op_list]


def get_all_dodge_op() -> List[ConditionalOperator]:
    """
    加载所有的闪避指令
    :return:
    """
    module_name_list = []
    dodge_dir_path = os_utils.get_path_under_work_dir('config', 'dodge')
    for file_name in os.listdir(dodge_dir_path):
        if file_name.endswith('.sample.yml'):
            module_name = file_name[:-11]
        elif file_name.endswith('.yml'):
            module_name = file_name[:-4]
        else:
            continue
        if module_name not in module_name_list:
            module_name_list.append(module_name)

    return [ConditionalOperator(module_name=module_name, sub_dir='dodge')
            for module_name in module_name_list]
