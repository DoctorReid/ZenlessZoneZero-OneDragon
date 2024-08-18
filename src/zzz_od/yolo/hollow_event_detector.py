import time

import csv
import numpy as np
import os
from cv2.typing import MatLike
from typing import Optional, List

from one_dragon.utils import yolo_config_utils
from one_dragon.utils.log_utils import log
from zzz_od.config.yolo_config import ZZZ_MODEL_DOWNLOAD_URL
from zzz_od.yolo import onnx_utils
from zzz_od.yolo.detect_utils import multiclass_nms, xywh2xyxy, DetectContext, DetectClass, DetectObjectResult, \
    DetectFrameResult
from zzz_od.yolo.onnx_model_loader import OnnxModelLoader


class HollowEventDetector(OnnxModelLoader):

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
        OnnxModelLoader.__init__(
            self,
            model_name=model_name,
            model_download_url=ZZZ_MODEL_DOWNLOAD_URL,
            model_parent_dir_path=model_parent_dir_path,
            gh_proxy=gh_proxy,
            personal_proxy=personal_proxy,
            gpu=gpu
        )

        self.keep_result_seconds: float = keep_result_seconds  # 保留识别结果的秒数
        self.run_result_history: List[DetectFrameResult] = []  # 历史识别结果

        self.idx_2_class: dict[int, DetectClass] = {}  # 分类
        self.class_2_idx: dict[str, int] = {}
        self._load_detect_classes(self.model_dir_path)

    def run(self, image: MatLike, conf: float = 0.6, iou: float = 0.5, run_time: Optional[float] = None) -> DetectFrameResult:
        """
        对图片进行识别
        :param image: 使用 opencv 读取的图片 BGR通道
        :param conf: 置信度阈值
        :return: 识别结果
        """
        t1 = time.time()
        context = DetectContext(image, run_time)
        context.conf = conf
        context.iou = iou

        input_tensor = self.prepare_input(context)
        t2 = time.time()

        outputs = self.inference(input_tensor)
        t3 = time.time()

        results = self.process_output(outputs, context)
        t4 = time.time()

        log.info(f'识别完毕 得到结果 {len(results)}个。预处理耗时 {t2 - t1:.3f}s, 推理耗时 {t3 - t2:.3f}s, 后处理耗时 {t4 - t3:.3f}s')

        return self.record_result(context, results)

    def prepare_input(self, context: DetectContext) -> np.ndarray:
        """
        推理前的预处理
        """
        input_tensor, scale_height, scale_width = onnx_utils.scale_input_image_u(context.img, self.onnx_input_width, self.onnx_input_height)
        context.scale_height = scale_height
        context.scale_width = scale_width
        return input_tensor

    def inference(self, input_tensor: np.ndarray):
        """
        图片输入到模型中进行推理
        :param input_tensor: 输入模型的图片 RGB通道
        :return: onnx模型推理得到的结果
        """
        outputs = self.session.run(self.output_names, {self.input_names[0]: input_tensor})
        return outputs

    def process_output(self, output, context: DetectContext) -> List[DetectObjectResult]:
        """
        :param output: 推理结果
        :param context: 上下文
        :return: 最终得到的识别结果
        """
        predictions = np.squeeze(output[0]).T

        keep = np.ones(shape=(predictions.shape[1]), dtype=bool)

        if context.labels is not None:
            keep[4:] = False  # 前4位是坐标 先把所有标签都设置为False
            if context.labels is not None:
                for label in context.labels:
                    idx = self.class_2_idx.get(label)
                    if idx is not None:
                        keep[idx + 4] = True

        predictions[:, keep == False] = 0

        # 按置信度阈值进行基本的过滤
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > context.conf, :]
        scores = scores[scores > context.conf]

        results: List[DetectObjectResult] = []
        if len(scores) == 0:
            return results

        # 选择置信度最高的类别
        class_ids = np.argmax(predictions[:, 4:], axis=1)

        # 提取Bounding box
        boxes = predictions[:, :4]  # 原始推理结果 xywh
        scale_shape = np.array([context.scale_width, context.scale_height, context.scale_width, context.scale_height])  # 缩放后图片的大小
        boxes = np.divide(boxes, scale_shape, dtype=np.float32)  # 转化到 0~1
        boxes *= np.array([context.img_width, context.img_height, context.img_width, context.img_height])  # 恢复到原图的坐标
        boxes = xywh2xyxy(boxes)  # 转化成 xyxy

        # 进行NMS 获取最后的结果
        indices = multiclass_nms(boxes, scores, class_ids, context.iou)

        for idx in indices:
            result = DetectObjectResult(rect=boxes[idx].tolist(),
                                        score=float(scores[idx]),
                                        detect_class=self.idx_2_class[int(class_ids[idx])]
                                        )
            results.append(result)

        return results

    def record_result(self, context: DetectContext, results: List[DetectObjectResult]) -> DetectFrameResult:
        """
        记录本帧识别结果
        :param context: 识别上下文
        :param results: 识别结果
        :return: 组合结果
        """
        new_frame = DetectFrameResult(
            raw_image=context.img,
            results=results,
            run_time=context.run_time
        )
        self.run_result_history.append(new_frame)
        self.run_result_history = [i for i in self.run_result_history
                                   if context.run_time - i.run_time <= self.keep_result_seconds]

        return new_frame

    @property
    def last_run_result(self) -> Optional[DetectFrameResult]:
        if len(self.run_result_history) > 0:
            return self.run_result_history[len(self.run_result_history) - 1]
        else:
            return None

    def _load_detect_classes(self, model_dir_path: str):
        """
        加载分类
        :param model_dir_path: model_dir_path: str
        :return:
        """
        csv_path = os.path.join(model_dir_path, 'labels.csv')
        with open(csv_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row[0] != 'idx':
                    c = DetectClass(int(row[0]), row[1])
                    self.idx_2_class[c.class_id] = c
                    self.class_2_idx[c.class_name] = c.class_id
