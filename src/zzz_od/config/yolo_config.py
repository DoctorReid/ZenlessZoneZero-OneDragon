from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import yolo_config_utils

ZZZ_MODEL_DOWNLOAD_URL = 'https://github.com/OneDragon-Anything/OneDragon-YOLO/releases/download/zzz_model'

_DEFAULT_FLASH_CLASSIFIER = 'yolov8n-640-flash-0127'
_BACKUP_FLASH_CLASSIFIER = 'yolov8n-640-flash-1215'

_DEFAULT_HOLLOW_ZERO_EVENT = 'yolov8s-736-hollow-zero-event-0126'
_BACKUP_HOLLOW_ZERO_EVENT = 'yolov8s-736-hollow-zero-event-1130'

_DEFAULT_LOST_VOID_DET = 'yolov8n-736-lost-void-det-0125'
_BACKUP_LOST_VOID_DET = 'yolov8n-736-lost-void-det-0113'


class YoloConfig(YamlConfig):

    def __init__(self):
        YamlConfig.__init__(self, 'yolo', instance_idx=None)

    @property
    def flash_classifier(self) -> str:
        """
        识别闪光模式 只允许使用最新的两个模型
        :return:
        """
        current = self.get('flash_classifier', _DEFAULT_FLASH_CLASSIFIER)
        if current != _DEFAULT_FLASH_CLASSIFIER and current != _BACKUP_FLASH_CLASSIFIER:
            current = _DEFAULT_FLASH_CLASSIFIER
            self.flash_classifier = _DEFAULT_FLASH_CLASSIFIER
        return current

    @flash_classifier.setter
    def flash_classifier(self, new_value: str) -> None:
        self.update('flash_classifier', new_value)

    @property
    def flash_classifier_backup(self) -> str:
        return _BACKUP_FLASH_CLASSIFIER

    @property
    def flash_classifier_gpu(self) -> bool:
        return self.get('flash_classifier_gpu', True)

    @flash_classifier_gpu.setter
    def flash_classifier_gpu(self, new_value: bool) -> None:
        self.update('flash_classifier_gpu', new_value)

    @property
    def hollow_zero_event(self) -> str:
        """
        枯萎之都格子模型 只允许使用最新的两个模型
        :return:
        """
        current = self.get('hollow_zero_event', _DEFAULT_HOLLOW_ZERO_EVENT)
        if current!= _DEFAULT_HOLLOW_ZERO_EVENT and current!= _BACKUP_HOLLOW_ZERO_EVENT:
            current = _DEFAULT_HOLLOW_ZERO_EVENT
            self.hollow_zero_event = _DEFAULT_HOLLOW_ZERO_EVENT
        return current

    @hollow_zero_event.setter
    def hollow_zero_event(self, new_value: str) -> None:
        self.update('hollow_zero_event', new_value)

    @property
    def hollow_zero_event_backup(self) -> str:
        return _BACKUP_HOLLOW_ZERO_EVENT

    @property
    def hollow_zero_event_gpu(self) -> bool:
        return self.get('hollow_zero_event_gpu', True)

    @hollow_zero_event_gpu.setter
    def hollow_zero_event_gpu(self, new_value: bool) -> None:
        self.update('hollow_zero_event_gpu', new_value)

    @property
    def lost_void_det(self) -> str:
        """
        迷失之地识别模型 只允许使用最新的两个模型
        :return:
        """
        current = self.get('lost_void_det', _DEFAULT_LOST_VOID_DET)
        if current!= _DEFAULT_LOST_VOID_DET and current!= _BACKUP_LOST_VOID_DET:
            current = _DEFAULT_LOST_VOID_DET
            self.lost_void_det = _DEFAULT_LOST_VOID_DET
        return current

    @lost_void_det.setter
    def lost_void_det(self, new_value: str) -> None:
        self.update('lost_void_det', new_value)

    @property
    def lost_void_det_backup(self) -> str:
        return _BACKUP_LOST_VOID_DET

    @property
    def lost_void_det_gpu(self) -> bool:
        return self.get('lost_void_det_gpu', True)

    @lost_void_det_gpu.setter
    def lost_void_det_gpu(self, new_value: bool) -> None:
        self.update('lost_void_det_gpu', new_value)

    def using_old_model(self) -> bool:
        """
        是否在使用旧模型
        :return:
        """
        return (self.flash_classifier != _DEFAULT_FLASH_CLASSIFIER
                or self.hollow_zero_event != _DEFAULT_HOLLOW_ZERO_EVENT
                or self.lost_void_det != _DEFAULT_LOST_VOID_DET
                )


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


def get_lost_void_det_opts() -> List[ConfigItem]:
    """
    获取迷失之地识别模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('lost_void_det')
    if _DEFAULT_LOST_VOID_DET not in models_list:
        models_list.append(_DEFAULT_LOST_VOID_DET)

    return [ConfigItem(i) for i in models_list]
