import os
from typing import List

from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils import os_utils


def get_operation_template_config_list() -> List[ConfigItem]:
    """
    获取用于配置页面显示的指令列表，支持子目录。
    :return: 配置页面的选项列表
    """
    op_list: List[OperationTemplate] = get_all_operation_template()
    return [ConfigItem(label=op.module_name, value=op.module_name) for op in op_list]



def get_all_operation_template() -> List[OperationTemplate]:
    """
    加载所有的自动战斗指令，支持递归查找子目录。
    :return: OperationTemplate 对象列表
    """
    auto_battle_dir_path = os_utils.get_path_under_work_dir('config', 'auto_battle_operation')

    template_name_set = set()

    # 递归查找所有 .yml 文件
    for root, dirs, files in os.walk(auto_battle_dir_path):
        for file_name in files:
            if file_name.endswith('.sample.yml'):
                template_name = os.path.join(root, file_name[:-11])  # 去掉 '.sample.yml'
            elif file_name.endswith('.yml'):
                template_name = os.path.join(root, file_name[:-4])  # 去掉 '.yml'
            else:
                continue

            # 转换为相对路径
            relative_template_name = os.path.relpath(template_name, auto_battle_dir_path).replace("\\", "/")
            template_name_set.add(relative_template_name)

    result_op_list = []
    for template_name in template_name_set:
        result_op_list.append(OperationTemplate('auto_battle_operation', template_name))

    return result_op_list


def get_operation_template_config_file_path(template_name: str) -> str:
    """
    自动战斗配置文件路径，支持子目录。
    :param template_name: 模板名称（包含子目录的相对路径）
    :return: 完整的模板文件路径
    """
    return os.path.join(
        os_utils.get_path_under_work_dir('config', 'auto_battle_operation'),
        f'{template_name}.yml'
    )

