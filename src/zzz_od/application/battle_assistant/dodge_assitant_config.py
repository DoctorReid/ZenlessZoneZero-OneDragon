import os

from typing import List, Optional

from one_dragon.base.conditional_operation.conditional_operator import ConditionalOperator
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils import os_utils


def get_dodge_op_config_list() -> List[ConfigItem]:
    """
    获取用于配置页面显示的指令列表
    :return:
    """
    op_list: List[ConditionalOperator] = get_all_dodge_op()
    return [ConfigItem(label=op.name, value=op.name)
            for op in op_list]


def get_all_dodge_op() -> List[ConditionalOperator]:
    """
    加载所有的闪避指令
    :return:
    """
    dodge_dir_path = os_utils.get_path_under_work_dir('config', 'dodge')

    op_name_set = set()
    op_name_map = {}
    op_name_sample_map = {}
    for file_name in os.listdir(dodge_dir_path):
        if file_name.endswith('.sample.yml'):
            is_sample = True
            module_name = file_name[:-4]
        elif file_name.endswith('.yml'):
            is_sample = False
            module_name = file_name[:-4]
        else:
            continue

        op = ConditionalOperator(module_name=module_name, sub_dir='dodge')
        op_name_set.add(op.name)
        if is_sample:
            op_name_sample_map[op.name] = op
        else:
            op_name_map[op.name] = op

    result_op_list = []
    for op_name in op_name_set:
        if op_name in op_name_map:
            result_op_list.append(op_name_map[op_name])
        else:
            result_op_list.append(op_name_sample_map[op_name])

    return result_op_list


def get_dodge_op_by_name(op_name: str) -> Optional[ConditionalOperator]:
    all_op = get_all_dodge_op()
    for op in all_op:
        if op.name == op_name:
            return op
    return None


def get_dodge_config_file_path(module_name: str) -> str:
    """
    闪避配置文件路径
    :param module_name:
    :return:
    """
    return os.path.join(
        os_utils.get_path_under_work_dir('config', 'dodge'),
        f'{module_name}.yml'
    )
