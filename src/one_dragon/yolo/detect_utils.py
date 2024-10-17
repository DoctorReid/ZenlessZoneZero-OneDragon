import time

import cv2
from typing import List, Optional, Tuple

import numpy as np
from cv2.typing import MatLike

_COLORS = np.random.default_rng(3).uniform(0, 255, size=(100, 3))


class DetectContext:

    def __init__(self, raw_image: MatLike, run_time: Optional[float] = None):
        """
        推理过程的上下文
        用于保存临时变量
        """
        self.run_time: float = time.time() if run_time is None else run_time
        """识别时间"""

        self.img: MatLike = raw_image
        """预测用的图片"""

        self.img_height: int = raw_image.shape[0]
        """原图的高度"""

        self.img_width: int = raw_image.shape[1]
        """原图的宽度"""

        self.labels: Optional[List[str]] = None
        """只检测特定的标签 见 labels.csv 的label"""

        self.conf: float = 0.7
        """检测时用的置信度阈值"""

        self.iou: float = 0.5
        """检测时用的IOU阈值"""

        self.scale_height: int = 0
        """缩放后的高度"""

        self.scale_width: int = 0
        """缩放后的宽度"""


class DetectClass:

    def __init__(self, class_id: int, class_name: str):
        """
        检测类别
        """
        self.class_id: int = class_id
        self.class_name: str = class_name


class DetectObjectResult:

    def __init__(self, rect: List,
                 score: float,
                 detect_class: DetectClass
                 ):
        """
        识别到的一个结果
        :param rect: 目标的位置 xyxy
        :param score: 得分（置信度）
        :param detect_class: 检测到的类别
        """
        self.x1: int = int(rect[0])
        """目标框的左上角x"""
        self.y1: int = int(rect[1])
        """目标框的左上角y"""
        self.x2: int = int(rect[2])
        """目标框的右下角x"""
        self.y2: int = int(rect[3])
        """目标框的右下角y"""

        self.score: float = score
        """得分（置信度）"""

        self.detect_class: DetectClass = detect_class
        """检测到的类别"""

    @property
    def center(self) -> Tuple[int, int]:
        """
        中心点的位置
        :return:
        """
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2


class DetectFrameResult:

    def __init__(self,
                 raw_image: MatLike,
                 results: List[DetectObjectResult],
                 run_time: Optional[float] = None,
                 ):
        """
        一帧画面的识别结果
        """
        self.run_time: float = time.time() if run_time is None else run_time
        """识别时间"""

        self.raw_image: MatLike = raw_image
        """识别的原始图片"""

        self.results: List[DetectObjectResult] = results
        """识别的结果"""


def nms(boxes, scores, iou_threshold):
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]

    keep_boxes = []
    while sorted_indices.size > 0:
        # Pick the last box
        box_id = sorted_indices[0]
        keep_boxes.append(box_id)

        # Compute IoU of the picked box with the rest
        ious = compute_iou(boxes[box_id, :], boxes[sorted_indices[1:], :])

        # Remove boxes with IoU over the threshold
        keep_indices = np.where(ious < iou_threshold)[0]

        # print(keep_indices.shape, sorted_indices.shape)
        sorted_indices = sorted_indices[keep_indices + 1]

    return keep_boxes


def multiclass_nms(boxes, scores, class_ids, iou_threshold):

    unique_class_ids = np.unique(class_ids)

    keep_boxes = []
    for class_id in unique_class_ids:
        class_indices = np.where(class_ids == class_id)[0]
        class_boxes = boxes[class_indices,:]
        class_scores = scores[class_indices]

        class_keep_boxes = nms(class_boxes, class_scores, iou_threshold)
        keep_boxes.extend(class_indices[class_keep_boxes])

    return keep_boxes


def compute_iou(box, boxes):
    # Compute xmin, ymin, xmax, ymax for both boxes
    xmin = np.maximum(box[0], boxes[:, 0])
    ymin = np.maximum(box[1], boxes[:, 1])
    xmax = np.minimum(box[2], boxes[:, 2])
    ymax = np.minimum(box[3], boxes[:, 3])

    # Compute intersection area
    intersection_area = np.maximum(0, xmax - xmin) * np.maximum(0, ymax - ymin)

    # Compute union area
    box_area = (box[2] - box[0]) * (box[3] - box[1])
    boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union_area = box_area + boxes_area - intersection_area

    # Compute IoU
    iou = intersection_area / union_area

    return iou


def xywh2xyxy(x):
    # Convert bounding box (x, y, w, h) to bounding box (x1, y1, x2, y2)
    y = np.copy(x)
    y[..., 0] = x[..., 0] - x[..., 2] / 2
    y[..., 1] = x[..., 1] - x[..., 3] / 2
    y[..., 2] = x[..., 0] + x[..., 2] / 2
    y[..., 3] = x[..., 1] + x[..., 3] / 2
    return y


def draw_detections(detect_result: DetectFrameResult, mask_alpha=0.3) -> MatLike:
    """
    在原图上绘制识别结果 返回一张新的图片
    :param detect_result:
    :param mask_alpha:
    :return:
    """
    image: MatLike = detect_result.raw_image
    results: List[DetectObjectResult] = detect_result.results
    det_img = image.copy()

    img_height, img_width = image.shape[:2]
    font_size = min([img_height, img_width]) * 0.0006
    text_thickness = int(min([img_height, img_width]) * 0.001)

    det_img = draw_masks(det_img, results, mask_alpha)

    # Draw bounding boxes and labels of detections
    for result in results:
        color = _COLORS[result.detect_class.class_id]

        cv2.rectangle(det_img, (result.x1, result.y1), (result.x2, result.y2), color, 2)

        label = result.detect_class
        caption = f'{label.class_name} {int(result.score * 100)}%'
        draw_text(det_img, caption, result, font_size, text_thickness)

    return det_img


def draw_text(image: np.ndarray, text: str, result: DetectObjectResult,
              font_size: float = 0.001, text_thickness: int = 2) -> np.ndarray:
    # opencv不支持中文 需要把中文字符置空
    import re
    text = re.sub(r'[\u4e00-\u9fa5]', '', text)
    x1, y1, x2, y2 = result.x1, result.y1, result.x2, result.y2
    color = _COLORS[result.detect_class.class_id]
    (tw, th), _ = cv2.getTextSize(text=text, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                  fontScale=font_size, thickness=text_thickness)
    th = int(th * 1.2)

    cv2.rectangle(image, (x1, y1),
                  (x1 + tw, y1 - th), color, -1)

    return cv2.putText(image, text, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, font_size, (255, 255, 255), text_thickness, cv2.LINE_AA)


def draw_masks(image: np.ndarray, results: List[DetectObjectResult], mask_alpha: float = 0.3) -> np.ndarray:
    mask_img = image.copy()

    # Draw bounding boxes and labels of detections
    for result in results:
        color = _COLORS[result.detect_class.class_id]

        # Draw fill rectangle in mask image
        cv2.rectangle(mask_img, (result.x1, result.y1), (result.x2, result.y2), color, -1)

    return cv2.addWeighted(mask_img, mask_alpha, image, 1 - mask_alpha, 0)
