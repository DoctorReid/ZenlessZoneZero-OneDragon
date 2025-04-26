import time

import os
from cv2.typing import MatLike
from typing import List

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.utils import os_utils
from one_dragon.utils import str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class RapidOcrMatcher(OcrMatcher):
    """
    使用onnx的ocr模型 速度更快
    TODO 未测试使用 RGB图片是否有影响
    """

    def __init__(self):
        OcrMatcher.__init__(self)
        self._model = None
        self._loading: bool = False

    def init_model(self) -> bool:
        log.info('正在加载OCR模型')
        while self._loading:
            time.sleep(1)
            return True
        self._loading = True

        if self._model is None:
            from rapidocr import RapidOCR
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'rapid_ocr')

            try:
                self._model = RapidOCR(
                    det_model_path=os.path.join(models_dir, 'det.onnx'),
                    rec_model_path=os.path.join(models_dir, 'rec.onnx'),
                    cls_model_path=os.path.join(models_dir, 'cls.onnx'),
                    rec_keys_path=os.path.join(models_dir, 'ppocr_keys_v1.txt'),
                )
                self._loading = False
                log.info('加载OCR模型完毕')
                return True
            except Exception:
                log.error('OCR模型加载出错', exc_info=True)
                self._loading = False
                return False

        log.info('加载OCR模型完毕')
        self._loading = False
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
        # RapidOCR.__call__ 返回 (ocr_res, elapse_list) 或 (None, None)
        ocr_result_tuple = self._model(image, use_det=True, use_cls=False, use_rec=True)
        if ocr_result_tuple is None or ocr_result_tuple[0] is None:
            log.debug('OCR 未识别到结果 耗时 %.2f', time.time() - start_time)
            return result_map

        scan_result, elapse_list = ocr_result_tuple
        # scan_result 结构: [[box.tolist(), text, score], ...]
        for anchor in scan_result:
            anchor_position_list = anchor[0]  # box.tolist()
            anchor_text = anchor[1]  # text
            anchor_score = anchor[2]  # score
            if threshold is not None and anchor_score < threshold:
                continue

            # 从 box.tolist() 提取坐标和尺寸
            # box 格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            # 近似取左上角和右下角计算 x, y, w, h
            x = min(p[0] for p in anchor_position_list)
            y = min(p[1] for p in anchor_position_list)
            w = max(p[0] for p in anchor_position_list) - x
            h = max(p[1] for p in anchor_position_list) - y

            if anchor_text not in result_map:
                result_map[anchor_text] = MatchResultList(only_best=False)
            result_map[anchor_text].append(MatchResult(anchor_score,
                                                       x, y, w, h,
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
        :return: 识别到的文本
        """
        start_time = time.time()
        # RapidOCR.__call__ 返回 (ocr_res, elapse_list) 或 (None, None)
        ocr_result_tuple = self._model(image, use_det=False, use_cls=False, use_rec=True)

        if ocr_result_tuple is None or ocr_result_tuple[0] is None:
            log.debug("OCR (无检测) 未识别到结果 耗时 %.2f", time.time() - start_time)
            return ""

        scan_result, elapse_list = ocr_result_tuple
        # scan_result 结构: [[text, score], ...]
        if not scan_result:
            log.debug("OCR (无检测) 结果列表为空 耗时 %.2f", time.time() - start_time)
            return ""

        # 通常只有一个结果，取第一个
        first_res = scan_result[0]
        text = first_res[0]
        score = first_res[1]

        if threshold is not None and score < threshold:
            log.debug("OCR (无检测) 模型返回的识别结果置信度 %.2f 低于阈值 %.2f", score, threshold)
            return ""

        log.debug('OCR (无检测) 结果 %s (%.2f) 耗时 %.2f', text, score, time.time() - start_time)
        return text

    def match_words(self, image: MatLike, words: List[str], threshold: float = None,
                    same_word: bool = False,
                    ignore_case: bool = True, lcs_percent: float = -1, merge_line_distance: float = -1) -> dict[
        str, MatchResultList]:
        """
        在图片中查找关键词 返回所有词对应的位置
        :param image: 图片
        :param words: 关键词
        :param threshold: 匹配阈值
        :param same_word: 要求整个词一样
        :param ignore_case: 忽略大小写
        :param lcs_percent: 最长公共子序列长度百分比 -1代表不使用 same_word=True时不生效
        :param merge_line_distance: 多少行距内合并结果 -1为不合并
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold, merge_line_distance=merge_line_distance)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                ocr_result: str = k
                ocr_target = gt(w, 'ocr')
                if ignore_case:
                    ocr_result = ocr_result.lower()
                    ocr_target = ocr_target.lower()

                if same_word:
                    if ocr_result == ocr_target:
                        match_key.add(k)
                else:
                    if lcs_percent == -1:
                        if ocr_result.find(ocr_target) != -1:
                            match_key.add(k)
                    else:
                        if str_utils.find_by_lcs(ocr_target, ocr_result, percent=lcs_percent):
                            match_key.add(k)

        return {key: all_match_result[key] for key in match_key if key in all_match_result}

