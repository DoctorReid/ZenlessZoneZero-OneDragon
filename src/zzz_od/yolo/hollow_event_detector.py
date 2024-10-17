import os
from typing import Optional, List

from one_dragon.yolo.detect_utils import DetectClass, DetectFrameResult
from one_dragon.yolo.yolov8_onnx_det import Yolov8Detector
from zzz_od.config.yolo_config import ZZZ_MODEL_DOWNLOAD_URL


class HollowEventDetector(Yolov8Detector):

    def __init__(self,
                 model_name: str = 'yolov8n-640-hollow-event',
                 model_parent_dir_path: Optional[str] = os.path.abspath(__file__),  # 默认使用本文件的目录
                 gh_proxy: bool = True,
                 personal_proxy: Optional[str] = '',
                 gpu: bool = False,
                 keep_result_seconds: float = 2
                 ):
        """
        崩铁用的YOLO模型 参考自 https://github.com/ibaiGorordo/ONNX-YOLOv8-Object-Detection
        :param model_name: 模型名称 在根目录下会有一个以模型名称创建的子文件夹
        :param model_parent_dir_path: 放置所有模型的根目录
        :param gpu: 是否启用GPU运算
        :param keep_result_seconds: 保留多长时间的识别结果
        """
        Yolov8Detector.__init__(
            self,
            model_name=model_name,
            model_parent_dir_path=model_parent_dir_path,
            model_download_url=ZZZ_MODEL_DOWNLOAD_URL,
            gh_proxy=gh_proxy,
            personal_proxy=personal_proxy,
            gpu=gpu
        )

        self.keep_result_seconds: float = keep_result_seconds  # 保留识别结果的秒数
        self.run_result_history: List[DetectFrameResult] = []  # 历史识别结果

        self.idx_2_class: dict[int, DetectClass] = {}  # 分类
        self.class_2_idx: dict[str, int] = {}
        self._load_detect_classes(self.model_dir_path)
