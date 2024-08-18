from one_dragon.base.config.yaml_config import YamlConfig

ZZZ_MODEL_DOWNLOAD_URL = 'https://github.com/DoctorReid/OneDragon-YOLO/releases/download/zzz_model'


class YoloConfig(YamlConfig):

    def __init__(self):
        YamlConfig.__init__(self, 'yolo', instance_idx=None)

    @property
    def flash_classifier(self) -> str:
        return self.get('flash_classifier', 'yolov8n-640-flash-0718')

    @flash_classifier.setter
    def flash_classifier(self, new_value: str) -> None:
        self.update('flash_classifier', new_value)

    @property
    def hollow_zero_event(self) -> str:
        return self.get('hollow_zero_event', 'yolov8s-640-hollow-zero-event-0818')

    @hollow_zero_event.setter
    def hollow_zero_event(self, new_value: str) -> None:
        self.update('hollow_zero_event', new_value)

