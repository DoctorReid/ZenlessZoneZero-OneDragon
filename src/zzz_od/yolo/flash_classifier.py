import os
from typing import Optional

from one_dragon.yolo.yolo_utils import ZZZ_MODEL_DOWNLOAD_URL
from one_dragon.yolo.yolov8_onnx_cls import Yolov8Classifier


class FlashClassifier(Yolov8Classifier):

    def __init__(self,
                 model_name: str = 'yolov8n-640-dodge-0718',
                 model_parent_dir_path: Optional[str] = os.path.abspath(__file__),  # 默认使用本文件的目录
                 gh_proxy: bool = True,
                 personal_proxy: Optional[str] = None,
                 gpu: bool = False,
                 keep_result_seconds: float = 2
                 ):
        """
        :param model_name: 模型名称 在根目录下会有一个以模型名称创建的子文件夹
        :param model_parent_dir_path: 放置所有模型的根目录
        :param gpu: 是否启用GPU加速
        :param keep_result_seconds: 保留多长时间的识别结果
        """
        Yolov8Classifier.__init__(
            self,
            model_name=model_name,
            model_parent_dir_path=model_parent_dir_path,
            model_download_url=ZZZ_MODEL_DOWNLOAD_URL,
            gh_proxy=gh_proxy,
            personal_proxy=personal_proxy,
            gpu=gpu,
            keep_result_seconds=keep_result_seconds
        )
