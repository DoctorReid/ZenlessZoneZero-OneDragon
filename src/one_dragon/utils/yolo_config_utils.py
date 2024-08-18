import os

from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils import os_utils


def get_model_category_dir(category: str) -> str:
    return os_utils.get_path_under_work_dir('assets', 'models', category)


def get_available_models(category: str) -> List[str]:
    """
    获取某文件夹下可用的模型列表
    """
    result_list: List[str] = []
    dir_path = get_model_category_dir(category)
    for sub_dir_name in os.listdir(dir_path):
        if is_model_existed(category, sub_dir_name):
            result_list.append(sub_dir_name)

    return result_list


def get_flash_classifier_opts() -> List[ConfigItem]:
    """
    获取闪光模型的选项
    :return:
    """
    models_list = get_available_models('flash_classifier') + [ 'yolov8n-640-flash-0718' ]

    return [ConfigItem(i) for i in models_list]


def get_hollow_zero_event_opts() -> List[ConfigItem]:
    """
    获取空洞模型的选项
    :return:
    """
    models_list = get_available_models('hollow_zero_event') + [ 'yolov8s-640-hollow-zero-event-0818' ]

    return [ConfigItem(i) for i in models_list]


def is_model_existed(category: str, model_name: str) -> bool:
    """
    判断模型是否存在
    :param category:
    :param model_name:
    :return:
    """
    dir_path = os_utils.get_path_under_work_dir('assets', 'models', category)
    model_dir_path = os.path.join(dir_path, model_name)
    if not os.path.exists(model_dir_path) or not os.path.isdir(model_dir_path):
        return False

    label_path = os.path.join(model_dir_path, 'labels.csv')
    model_path = os.path.join(model_dir_path, 'model.onnx')

    return os.path.exists(label_path) and os.path.exists(model_path)
