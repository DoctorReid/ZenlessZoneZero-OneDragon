import time
import threading
from concurrent.futures import ThreadPoolExecutor
import os
from cv2.typing import MatLike
from typing import Callable, List, Optional, Any

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.matcher.ocr import ocr_utils
from one_dragon.base.matcher.ocr.ocr_matcher import OcrMatcher
from one_dragon.base.web.common_downloader import CommonDownloaderParam
from one_dragon.base.web.zip_downloader import ZipDownloader
from one_dragon.utils import os_utils
from one_dragon.utils import str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


DEFAULT_OCR_MODEL_NAME: str = 'ppocrv5'
GITHUB_DOWNLOAD_URL: str = 'https://github.com/OneDragon-Anything/OneDragon-Env/releases/download'
GITEE_DOWNLOAD_URL: str = 'https://gitee.com/OneDragon-Anything/OneDragon-Env/releases/download'

# 全局模型实例缓存，避免重复加载
_global_model_cache: dict[str, Any] = {}
_model_cache_lock = threading.Lock()


def get_ocr_model_dir(ocr_model_name: str) -> str:
    return os_utils.get_path_under_work_dir('assets', 'models', 'onnx_ocr', ocr_model_name)


def get_ocr_download_url_github(ocr_model_name: str) -> str:
    return get_ocr_download_url(GITHUB_DOWNLOAD_URL, ocr_model_name)


def get_ocr_download_url_gitee(ocr_model_name: str) -> str:
    return get_ocr_download_url(GITEE_DOWNLOAD_URL, ocr_model_name)


def get_ocr_download_url(website: str, ocr_model_name: str) -> str:
    return f'{website}/{ocr_model_name}/{ocr_model_name}.zip'


def get_final_file_list(ocr_model_name: str) -> list[str]:
    """
    下载成功后 整个模型的所有文件
    :param ocr_model_name: 模型名称
    :return:
    """
    base_dir = get_ocr_model_dir(ocr_model_name)
    return [
        os.path.join(base_dir, 'det.onnx'),
        os.path.join(base_dir, 'rec.onnx'),
        os.path.join(base_dir, 'cls.onnx'),
        os.path.join(base_dir, 'ppocrv5_dict.txt'),
        os.path.join(base_dir, 'simfang.ttf'),
    ]


class OnnxOcrMatcher(OcrMatcher, ZipDownloader):
    """
    使用onnx的ocr模型 速度更快
    """

    def __init__(self, ocr_model_name: str = DEFAULT_OCR_MODEL_NAME):
        self.ocr_model_name = ocr_model_name
        self.base_dir: str = get_ocr_model_dir(ocr_model_name)
        OcrMatcher.__init__(self)
        param = CommonDownloaderParam(
            save_file_path=self.base_dir,
            save_file_name=f'{ocr_model_name}.zip',
            github_release_download_url=get_ocr_download_url_github(ocr_model_name),
            gitee_release_download_url=get_ocr_download_url_gitee(ocr_model_name),
            mirror_chan_download_url='',
            check_existed_list=get_final_file_list(ocr_model_name)
        )
        ZipDownloader.__init__(
            self,
            param=param,
        )
        self._model: Optional[Any] = None
        self._loading: bool = False
        self._init_future = None  # 异步初始化的Future对象
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='ocr-init')

    def init_model(
            self,
            download_by_github: bool = True,
            download_by_gitee: bool = False,
            download_by_mirror_chan: bool = False,
            proxy_url: Optional[str] = None,
            ghproxy_url: Optional[str] = None,
            skip_if_existed: bool = True,
            progress_callback: Optional[Callable[[float, str], None]] = None,
            async_init: bool = True  # 新增参数：是否异步初始化
    ) -> bool:
        """
        初始化OCR模型
        :param async_init: 是否异步初始化模型，True时立即返回，后台加载；False时同步等待加载完成
        """
        log.info('正在加载OCR模型')

        # 检查全局缓存
        with _model_cache_lock:
            if self.ocr_model_name in _global_model_cache:
                self._model = _global_model_cache[self.ocr_model_name]
                log.info('使用缓存的OCR模型')
                return True

        # 保证只有一个线程下载和初始化
        if self._loading:
            if async_init and self._init_future:
                return True  # 异步模式下，如果正在加载则直接返回
            else:
                # 同步等待加载完成
                while self._loading:
                    time.sleep(0.1)
                return self._model is not None

        self._loading = True

        if async_init:
            # 异步初始化
            self._init_future = self._executor.submit(self._init_model_sync,
                                                      download_by_github, download_by_gitee,
                                                      download_by_mirror_chan, proxy_url,
                                                      ghproxy_url, skip_if_existed, progress_callback)
            return True
        else:
            # 同步初始化
            return self._init_model_sync(download_by_github, download_by_gitee,
                                         download_by_mirror_chan, proxy_url,
                                         ghproxy_url, skip_if_existed, progress_callback)

    def _init_model_sync(self, download_by_github, download_by_gitee, download_by_mirror_chan,
                         proxy_url, ghproxy_url, skip_if_existed, progress_callback) -> bool:
        """同步初始化模型的内部方法"""
        try:
            # 先检查模型文件和下载模型
            done: bool = self.download(
                download_by_github=download_by_github,
                download_by_gitee=download_by_gitee,
                download_by_mirror_chan=download_by_mirror_chan,
                proxy_url=proxy_url,
                ghproxy_url=ghproxy_url,
                skip_if_existed=skip_if_existed,
                progress_callback=progress_callback
            )
            if not done:
                log.error('下载OCR模型失败')
                return False

            # 加载模型
            if self._model is None:
                # 检查全局缓存（可能其他线程已经加载了）
                with _model_cache_lock:
                    if self.ocr_model_name in _global_model_cache:
                        self._model = _global_model_cache[self.ocr_model_name]
                        log.info('使用其他线程缓存的OCR模型')
                        return True

                from onnxocr.onnx_paddleocr import ONNXPaddleOcr

                try:
                    log.info('开始初始化ONNX OCR模型...')
                    model_start_time = time.time()

                    self._model = ONNXPaddleOcr(
                        use_angle_cls=False, use_gpu=False,
                        det_model_dir=os.path.join(self.base_dir, 'det.onnx'),
                        rec_model_dir=os.path.join(self.base_dir, 'rec.onnx'),
                        cls_model_dir=os.path.join(self.base_dir, 'cls.onnx'),
                        rec_char_dict_path=os.path.join(self.base_dir, 'ppocrv5_dict.txt'),
                        vis_font_path=os.path.join(self.base_dir, 'simfang.ttf'),
                    )

                    # 存储到全局缓存
                    with _model_cache_lock:
                        _global_model_cache[self.ocr_model_name] = self._model

                    model_load_time = time.time() - model_start_time
                    log.info(f'OCR模型初始化完成，耗时 {model_load_time:.2f}秒')

                    # 模型预热 - 使用小图片进行一次推理以优化后续性能
                    self._warmup_model()

                    return True
                except Exception:
                    log.error('OCR模型加载出错', exc_info=True)
                    return False

            log.info('OCR模型已加载')
            return True
        finally:
            self._loading = False

    def _warmup_model(self):
        """模型预热，提升后续推理速度"""
        try:
            import numpy as np
            # 创建一个小的测试图片进行预热
            warmup_img = np.ones((32, 100, 3), dtype=np.uint8) * 255
            warmup_start = time.time()
            if self._model is not None:
                self._model.ocr(warmup_img, cls=False)
            warmup_time = time.time() - warmup_start
            log.info(f'OCR模型预热完成，耗时 {warmup_time:.2f}秒')
        except Exception:
            log.warning('OCR模型预热失败，但不影响正常使用', exc_info=True)

    def _ensure_model_ready(self) -> bool:
        """确保模型已准备就绪"""
        if self._model is not None:
            return True

        if self._init_future and not self._init_future.done():
            log.info('等待OCR模型异步加载完成...')
            try:
                result = self._init_future.result(timeout=30)  # 最多等待30秒
                return result
            except Exception as e:
                log.error(f'等待OCR模型加载超时: {e}')
                return False

        # 如果没有异步初始化，尝试同步初始化
        if not self._loading:
            return self.init_model(async_init=False)

        return False

    def run_ocr_single_line(self, image: MatLike, threshold: float = 0, strict_one_line: bool = True) -> str:
        """
        单行文本识别 手动合成一行 按匹配结果从左到右 从上到下
        理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :param image: 图片
        :param threshold: 阈值
        :param strict_one_line: True时认为当前只有单行文本 False时依赖程序合并成一行
        :return:
        """
        if not self._ensure_model_ready():
            log.error('OCR模型未准备就绪')
            return ""

        if strict_one_line:
            return self._run_ocr_without_det(image, threshold)
        else:
            ocr_map: dict = self.run_ocr(image, threshold)
            tmp = ocr_utils.merge_ocr_result_to_single_line(ocr_map, join_space=False)
            return tmp

    def run_ocr(self, image: MatLike, threshold: float = 0,
                merge_line_distance: float = -1) -> dict[str, MatchResultList]:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :param merge_line_distance: 多少行距内合并结果 -1为不合并 理论中文情况不会出现过长分行的 这里只是为了兼容英语的情况
        :return: {key_word: []}
        """
        if not self._ensure_model_ready():
            log.error('OCR模型未准备就绪')
            return {}

        start_time = time.time()
        result_map: dict = {}
        if self._model is not None:
            scan_result_list: list = self._model.ocr(image, cls=False)
            if len(scan_result_list) == 0:
                log.debug('OCR结果 %s 耗时 %.2f', result_map.keys(), time.time() - start_time)
                return result_map

            scan_result = scan_result_list[0]
            for anchor in scan_result:
                anchor_position = anchor[0]
                anchor_text = anchor[1][0]
                anchor_score = anchor[1][1]
                if anchor_score < threshold:
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

    def _run_ocr_without_det(self, image: MatLike, threshold: float = 0) -> str:
        """
        不使用检测模型分析图片内文字的分布
        默认传入的图片仅有文字信息
        :param image: 图片
        :param threshold: 匹配阈值
        :return: [[("text", "score"),]] 由于禁用了空格，可以直接取第一个元素
        """
        start_time = time.time()
        if self._model is not None:
            scan_result: list = self._model.ocr(image, det=False, cls=False)
            if len(scan_result) == 0:
                log.debug('OCR结果 空 耗时 %.2f', time.time() - start_time)
                return ''

            img_result = scan_result[0]  # 取第一张图片的结果
            if len(img_result) > 1:
                log.debug("禁检测的OCR模型返回多个识别结果")  # 目前没有出现这种情况

            if len(img_result) > 0 and img_result[0][1] >= threshold:
                text = img_result[0][0]
                log.debug('OCR结果 %s 置信度 %.2f 耗时 %.2f', text, img_result[0][1], time.time() - start_time)
                return text

        log.debug('OCR结果 空 耗时 %.2f', time.time() - start_time)
        return ''

    def match_words(
            self,
            image: MatLike, words: List[str],
            threshold: float = 0,
            same_word: bool = False,
            ignore_case: bool = True,
            lcs_percent: float = -1,
            merge_line_distance: float = -1
    ) -> dict[str, MatchResultList]:
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
        if not self._ensure_model_ready():
            log.error('OCR模型未准备就绪')
            return {}

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


def __debug():
    from one_dragon.utils import debug_utils
    matcher = OnnxOcrMatcher()
    matcher.init_model(async_init=False)  # 同步初始化以便调试

    img = debug_utils.get_debug_image('1')
    s = time.time()
    result = matcher.run_ocr(img)
    e = time.time()
    print("total time: {:.3f}".format(e - s))
    print("result:", result)

    # 测试单行识别
    single_result = matcher.run_ocr_single_line(img)
    print("single_result:", single_result)


if __name__ == "__main__":
    __debug()
