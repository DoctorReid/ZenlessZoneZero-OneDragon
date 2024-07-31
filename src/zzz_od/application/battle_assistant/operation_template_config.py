import os
from typing import List

from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils import os_utils


def get_operation_template_config_list() -> List[ConfigItem]:
    """
    获取用于配置页面显示的指令列表
    :return:
    """
    op_list: List[OperationTemplate] = get_all_operation_template()
    return [ConfigItem(label=op.module_name, value=op.module_name)
            for op in op_list]


def get_all_operation_template() -> List[OperationTemplate]:
    """
    加载所有的自动战斗指令
    :return:
    """
    auto_battle_dir_path = os_utils.get_path_under_work_dir('config', 'auto_battle_operation')

    template_name_set = set()
    for file_name in os.listdir(auto_battle_dir_path):
        if file_name.endswith('.sample.yml'):
            template_name = file_name[:-11]
        elif file_name.endswith('.yml'):
            template_name = file_name[:-4]
        else:
            continue

        template_name_set.add(template_name)

    result_op_list = []
    for template_name in template_name_set:
        result_op_list.append(OperationTemplate('auto_battle_operation', template_name))

    return result_op_list


def get_operation_template_config_file_path(template_name: str) -> str:
    """
    自动战斗配置文件路径
    :param template_name:
    :return:
    """
    return os.path.join(
        os_utils.get_path_under_work_dir('config', 'auto_battle_operation'),
        f'{template_name}.yml'
    )
