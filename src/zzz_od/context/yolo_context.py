from cv2.typing import MatLike
from enum import Enum

from one_dragon.base.operation.context_event_bus import ContextEventBus
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log
from zzz_od.yolo.dodge_classifier import DodgeClassifier


class YoloStateEventEnum(Enum):

    DODGE_YELLOW = '闪避识别-黄光'
    DODGE_RED = '闪避识别-红光'


class YoloContext:

    def __init__(self, event_bus: ContextEventBus):
        self._event_bus = event_bus
        self._dodge_model: DodgeClassifier = None

    def init_dodge_model(self, use_gpu: bool = True):
        self._dodge_model = DodgeClassifier(
            model_name='test1',
            model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo'),
            gpu=use_gpu
        )

    def should_dodge(self, screen: MatLike, screenshot_time: float, use_gpu: bool = True) -> bool:
        if self._dodge_model is None or self._dodge_model.gpu != use_gpu:
            self.init_dodge_model(use_gpu)
        result = self._dodge_model.run(screen)
        if result.class_idx == 1:
            e = YoloStateEventEnum.DODGE_RED.value
            log.info(e)
            self._event_bus.dispatch_event(e, screenshot_time)
            return True
        elif result.class_idx == 2:
            e = YoloStateEventEnum.DODGE_YELLOW.value
            log.info(e)
            self._event_bus.dispatch_event(e, screenshot_time)
            return True
        else:
            return False
