from cv2.typing import MatLike

from one_dragon.utils import os_utils
from zzz_od.yolo.dodge_classifier import DodgeClassifier


class YoloContext:

    def __init__(self):
        self._dodge_model: DodgeClassifier = None

    def init_dodge_model(self):
        if self._dodge_model is None:
            self._dodge_model = DodgeClassifier(
                model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo')
            )

    def should_dodge(self, screen: MatLike) -> bool:
        self.init_dodge_model()
        result = self._dodge_model.run(screen)
        return result.class_idx in [1, 2]
