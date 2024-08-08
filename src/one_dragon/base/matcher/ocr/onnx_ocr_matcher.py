import time

import os
from cv2.typing import MatLike

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


class OnnxOcrMatcher(OcrMatcher):
    """
    使用onnx的ocr模型 速度更快
    TODO 未测试使用 RGB图片是否有影响
    """

    def __init__(self):
        OcrMatcher.__init__(self)
        self._model = None

    def init_model(self) -> bool:
        log.info('正在加载OCR模型')

        if self._model is None:
            from onnxocr.onnx_paddleocr import ONNXPaddleOcr
            models_dir = os_utils.get_path_under_work_dir('assets', 'models', 'onnx_ocr')

            try:
                self._model = ONNXPaddleOcr(
                    use_angle_cls=False, use_gpu=False,
                    det_model_dir=os.path.join(models_dir, 'det.onnx'),
                    rec_model_dir=os.path.join(models_dir, 'rec.onnx'),
                    cls_model_dir=os.path.join(models_dir, 'cls.onnx'),
                    rec_char_dict_path=os.path.join(models_dir, 'ppocr_keys_v1.txt'),
                    vis_font_path=os.path.join(models_dir, 'simfang.tt'),
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
        scan_result_list: list = self._model.ocr(image, cls=False)
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
        scan_result: list = self._model.ocr(image, det=False, cls=False)
        img_result = scan_result[0]  # 取第一张图片
        if len(img_result) > 1:
            log.debug("禁检测的OCR模型返回多个识别结果")  # 目前没有出现这种情况

        if threshold is not None and scan_result[0][1] < threshold:
            log.debug("OCR模型返回的识别结果置信度低于阈值")
            return ""
        log.debug('OCR结果 %s 耗时 %.2f', scan_result, time.time() - start_time)
        return img_result[0][0]


if __name__ == '__main__':
    import os
    from one_dragon.utils import os_utils, debug_utils

    model = OnnxOcrMatcher()
    model.init_model()
    img = debug_utils.get_debug_image('1')
    t1 = time.time()
    result = model.run_ocr(img)
    t2 = time.time()
    print(result, t2-t1)
    result = model.run_ocr_single_line(img)
    t3 = time.time()
    print(result, t3-t2)
