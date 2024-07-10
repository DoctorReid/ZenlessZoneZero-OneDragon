from cv2.typing import MatLike

from one_dragon.utils import os_utils
from zzz_od.yolo.switch_classifier import SwitchClassifier


class YoloContext:

    def __init__(self):
        self._switch_model: SwitchClassifier = None

    def init_switch_model(self):
        if self._switch_model is None:
            self._switch_model = SwitchClassifier(
                model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo')
            )

    def should_switch(self, screen: MatLike) -> bool:
        self.init_switch_model()
        result = self._switch_model.run(screen)
        return result.class_idx in [1, 2]
