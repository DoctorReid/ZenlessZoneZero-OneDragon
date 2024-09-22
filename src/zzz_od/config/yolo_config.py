from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import yolo_config_utils

ZZZ_MODEL_DOWNLOAD_URL = 'https://github.com/DoctorReid/OneDragon-YOLO/releases/download/zzz_model'
_DEFAULT_FLASH_CLASSIFIER = 'yolov8n-640-flash-0718'
_DEFAULT_HOLLOW_ZERO_EVENT = 'yolov8s-736-hollow-zero-event-0922'


class YoloConfig(YamlConfig):

    def __init__(self):
        YamlConfig.__init__(self, 'yolo', instance_idx=None)

    @property
    def flash_classifier(self) -> str:
        return self.get('flash_classifier', _DEFAULT_FLASH_CLASSIFIER)

    @flash_classifier.setter
    def flash_classifier(self, new_value: str) -> None:
        self.update('flash_classifier', new_value)

    @property
    def hollow_zero_event(self) -> str:
        return self.get('hollow_zero_event', _DEFAULT_HOLLOW_ZERO_EVENT)

    @hollow_zero_event.setter
    def hollow_zero_event(self, new_value: str) -> None:
        self.update('hollow_zero_event', new_value)

    def using_old_model(self) -> bool:
        """
        是否在使用旧模型
        :return:
        """
        return self.flash_classifier != _DEFAULT_FLASH_CLASSIFIER or self.hollow_zero_event != _DEFAULT_HOLLOW_ZERO_EVENT


def get_flash_classifier_opts() -> List[ConfigItem]:
    """
    获取闪光模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('flash_classifier')
    if _DEFAULT_FLASH_CLASSIFIER not in models_list:
        models_list.append(_DEFAULT_FLASH_CLASSIFIER)

    return [ConfigItem(i) for i in models_list]


def get_hollow_zero_event_opts() -> List[ConfigItem]:
    """
    获取空洞模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('hollow_zero_event')
    if _DEFAULT_HOLLOW_ZERO_EVENT not in models_list:
        models_list.append(_DEFAULT_HOLLOW_ZERO_EVENT)

    return [ConfigItem(i) for i in models_list]
