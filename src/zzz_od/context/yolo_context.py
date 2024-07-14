from cv2.typing import MatLike

from one_dragon.utils import os_utils
from zzz_od.yolo.dodge_classifier import DodgeClassifier


class YoloContext:

    def __init__(self):
        self._dodge_model: DodgeClassifier = None

    def init_dodge_model(self, use_gpu: bool = True):
        self._dodge_model = DodgeClassifier(
            model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo'),
            gpu=use_gpu
        )

    def should_dodge(self, screen: MatLike, use_gpu: bool = True) -> bool:
        if self._dodge_model is None or self._dodge_model.gpu != use_gpu:
            self.init_dodge_model(use_gpu)
        result = self._dodge_model.run(screen)
        return result.class_idx in [1, 2]
