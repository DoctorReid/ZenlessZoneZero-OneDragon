import time

import logging
import os
from cv2.typing import MatLike

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


class PaddleOcrMatcher(OcrMatcher):
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
        OcrMatcher.__init__(self)
        self.ocr = None

    def init_model(self) -> bool:
        log.info('正在加载OCR模型')

        if self.ocr is None:
            from paddleocr import PaddleOCR
            logging.getLogger().handlers.clear()  # 不知道为什么 这里会引入这个logger 清除掉避免console中有重复日志
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'ocr')

            try:
                self.ocr = PaddleOCR(
                    use_angle_cls=False, use_gpu=False, drop_score=0.5,
                    det_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_det_infer'),
                    rec_model_dir=os.path.join(models_dir, 'ch_PP-OCRv4_rec_infer'),
                    cls_model_dir=os.path.join(models_dir, 'ch_ppocr_mobile_v2.0_cls_slim_infer')
                )
                return True
            except Exception:
                log.error('OCR模型加载出错', exc_info=True)
                return False

        return True

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
            tmp = ocr_utils.merge_ocr_result_to_single_line(ocr_map, join_space=False)
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
        result_map: dict = {}
        scan_result_list: list = self.ocr.ocr(image, cls=False)
        if len(scan_result_list) == 0:
            log.debug('OCR结果 %s 耗时 %.2f', result_map.keys(), time.time() - start_time)
            return result_map

        scan_result = scan_result_list[0]
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
            result_map = ocr_utils.merge_ocr_result_to_multiple_line(result_map, join_space=True,
                                                                     merge_line_distance=merge_line_distance)
        log.debug('OCR结果 %s 耗时 %.2f', result_map.keys(), time.time() - start_time)
        return result_map

    def _run_ocr_without_det(self, image: MatLike, threshold: float = None) -> str:
        """
        不使用检测模型分析图片内文字的分布
        默认传入的图片仅有文字信息
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [[("text", "score"),]] 由于禁用了空格，可以直接取第一个元素
        """
        start_time = time.time()
        scan_result: list = self.ocr.ocr(image, det=False, cls=False)
        img_result = scan_result[0]  # 取第一张图片
        if len(img_result) > 1:
            log.debug("禁检测的OCR模型返回多个识别结果")  # 目前没有出现这种情况

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("OCR模型返回的识别结果置信度低于阈值")
            return ""
        log.debug('OCR结果 %s 耗时 %.2f', scan_result, time.time() - start_time)
        return img_result[0][0]
