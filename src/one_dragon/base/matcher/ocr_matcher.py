import logging
import os
import time
from typing import Optional, List

from cv2.typing import MatLike
from paddleocr import PaddleOCR

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log

logging.getLogger().handlers.clear()  # 不知道为什么 这里会引入这个logger 清除掉避免console中有重复日志


class OcrMatcher:
    """
    https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_ch/quickstart.md
    ocr.ocr(img) 返回的是一个list, for example:
    [
        [ [[894.0, 252.0], [1024.0, 252.0], [1024.0, 288.0], [894.0, 288.0]], ('快速恢复', 0.9989572763442993)],
        [ [[450.0, 494.0], [560.0, 494.0], [560.0, 530.0], [450.0, 530.0]], ('奇巧零食', 0.9995825290679932)]
    ]
    返回锚框的坐标是[[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
    不能并发使用，会有线程安全问题
    enable_mkldnn=True 后更慢了 原因未知
    应该尽量避免传入还有不明黑点或横线之类的被识别为标点符号
    使用识别祝福部分测试 传入黑白图并不能提速。颜色扣取不好还会导致识别精度下降。
    """

    def __init__(self):
        self.ocr: Optional[PaddleOCR] = None
        try:
            # 不使用方向检测, CPU推理, drop_score控制识别模型的精度,模型默认0.5 (rec)
            # 不启用空格识别 (rec) 文字空间结构交给 det 处理
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'ocr')

            self.ocr = PaddleOCR(use_angle_cls=False, lang="ch", use_gpu=False, use_space_char=False, drop_score=0.5,
                                 det_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_det_infer'),
                                 rec_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_rec_infer'),
                                 cls_model_dir=os.path.join(models_dir, 'ch_ppocr_mobile_v2.0_cls_slim_infer')
                                 )
        except Exception:
            log.error('OCR模型加载出错', exc_info=True)

    def run_ocr_single_line(self, image: MatLike, threshold: float = None, strict_one_line: bool = True) -> str:
        """
        单行文本识别 手动合成一行 按匹配结果从左到右 从上到下
        理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: True时认为当前只有单行文本 False时依赖程序合并成一行
        :return:
        """
        if strict_one_line:
            return self._run_ocr_without_det(image, threshold)
        else:
            ocr_map: dict = self.run_ocr(image, threshold)
            tmp = merge_ocr_result_to_single_line(ocr_map, join_space=False)
            return tmp

    def run_ocr(self, image: MatLike, threshold: float = None,
                merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :param merge_line_distance: 多少行距内合并结果 -1为不合并 理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :return: {key_word: []}
        """
        start_time = time.time()
        scan_result: list = self.ocr.ocr(image, cls=False)

        result_map: dict = {}
        for anchor in scan_result:
            anchor_position = anchor[0]
            anchor_text = anchor[1][0]
            anchor_score = anchor[1][1]
            if threshold is not None and anchor_score < threshold:
                continue
            if anchor_text not in result_map:
                result_map[anchor_text] = MatchResultList(only_best=False)
            result_map[anchor_text].append(MatchResult(anchor_score,
                                                       anchor_position[0][0],
                                                       anchor_position[0][1],
                                                       anchor_position[1][0] - anchor_position[0][0],
                                                       anchor_position[3][1] - anchor_position[0][1],
                                                       data=anchor_text))

        if merge_line_distance != -1:
            result_map = merge_ocr_result_to_multiple_line(result_map, join_space=True,
                                                           merge_line_distance=merge_line_distance)
        log.debug('OCR结果 %s 耗时 %.2f', result_map.keys(), time.time() - start_time)
        return result_map

    def _run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        不使用检测模型分析图片内文字的分布
        默认传入的图片仅有文字信息
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [("text", "score"),] 由于禁用了空格，可以直接取第一个元素
        """
        start_time = time.time()
        scan_result: list = self.ocr.ocr(image, det=False, cls=False)
        if len(scan_result) > 1:
            log.debug("禁检测的OCR模型返回多个识别结果")  # 目前没有出现这种情况

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("OCR模型返回的识别结果置信度低于阈值")
            return ""
        log.debug('OCR结果 %s 耗时 %.2f', scan_result, time.time() - start_time)
        return scan_result[0][0]


def merge_ocr_result_to_single_line(ocr_map, join_space: bool = True) -> str:
    """
    将OCR结果合并成一行 用于过长的文体产生换行
    :param ocr_map: run_ocr的结果
    :param join_space: 连接时是否加入空格
    :return:
    """
    lines: List[List[MatchResult]] = []
    for text, result_list in ocr_map.items():
        for result in result_list:
            in_line: int = -1
            for line_idx in range(len(lines)):
                for line_item in lines[line_idx]:
                    if abs(line_item.center.y - result.center.y) <= 5:
                        in_line = line_idx
                        break
                if in_line != -1:
                    break

            if in_line == -1:
                lines.append([result])
            else:
                lines[in_line].append(result)

    result_str: str = None
    for line in lines:
        sorted_line = sorted(line, key=lambda x: x.center.x)
        for result_item in sorted_line:
            if result_str is None:
                result_str = result_item.data
            else:
                result_str += (' ' if join_space else '') + result_item.data

    return result_str


def merge_ocr_result_to_multiple_line(ocr_map, join_space: bool = True, merge_line_distance: float = 40) -> dict[str, MatchResultList]:
    """
    将OCR结果合并成多行 用于过长的文体产生换行
    :param ocr_map: run_ocr的结果
    :param join_space: 连接时是否加入空格
    :param merge_line_distance: 多少行距内合并结果
    :return:
    """
    lines = []
    for text, result_list in ocr_map.items():
        for result in result_list:
            in_line: int = -1
            for line_idx in range(len(lines)):
                for line_item in lines[line_idx]:
                    if abs(line_item.center.y - result.center.y) <= merge_line_distance:
                        in_line = line_idx
                        break
                if in_line != -1:
                    break

            if in_line == -1:
                lines.append([result])
            else:
                lines[in_line].append(result)

    merge_ocr_result_map: dict[str, MatchResultList] = {}
    for line in lines:
        line_ocr_map = {}
        merge_result: MatchResult = MatchResult(1, 9999, 9999, 0, 0)
        for ocr_result in line:
            if ocr_result.data not in line_ocr_map:
                line_ocr_map[ocr_result.data] = MatchResultList()
            line_ocr_map[ocr_result.data].append(ocr_result)

            if ocr_result.x < merge_result.x:
                merge_result.x = ocr_result.x
            if ocr_result.y < merge_result.y:
                merge_result.y = ocr_result.y
            if ocr_result.x + ocr_result.w > merge_result.x + merge_result.w:
                merge_result.w = ocr_result.x + ocr_result.w - merge_result.x
            if ocr_result.y + ocr_result.h > merge_result.y + merge_result.h:
                merge_result.h = ocr_result.y + ocr_result.h - merge_result.y

        merge_result.data = merge_ocr_result_to_single_line(line_ocr_map, join_space=join_space)
        if merge_result.data not in merge_ocr_result_map:
            merge_ocr_result_map[merge_result.data] = MatchResultList()
        merge_ocr_result_map[merge_result.data].append(merge_result)

    return merge_ocr_result_map
