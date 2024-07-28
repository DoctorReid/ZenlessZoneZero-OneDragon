from concurrent.futures import ThreadPoolExecutor, Future

import threading
from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.utils import os_utils, thread_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.yolo.dodge_classifier import DodgeClassifier

_yolo_check_executor = ThreadPoolExecutor(thread_name_prefix='od_yolo_check', max_workers=16)


class YoloStateEventEnum(Enum):

    DODGE_YELLOW = '闪避识别-黄光'
    DODGE_RED = '闪避识别-红光'


class YoloContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx
        self._dodge_model: Optional[DodgeClassifier] = None

        # 识别锁 保证每种类型只有1实例在进行识别
        self._check_dodge_flash_lock = threading.Lock()

    def init_context(self, use_gpu: bool = True) -> None:
        """
        运行前 初始化上下文
        :return:
        """
        if self._dodge_model is None or self._dodge_model.gpu != use_gpu:
            self._dodge_model = DodgeClassifier(
                model_parent_dir_path=os_utils.get_path_under_work_dir('assets', 'models', 'yolo'),
                gpu=use_gpu
            )

    def check_screen(self, screen: MatLike, screenshot_time: float, sync: bool = False) -> None:
        """
        异步识别画面
        :return:
        """
        future_list: List[Future] = []
        future_list.append(_yolo_check_executor.submit(self.check_dodge_flash, screen, screenshot_time))

        for future in future_list:
            future.add_done_callback(thread_utils.handle_future_result)

        if sync:
            for future in future_list:
                future.result()

    def check_dodge_flash(self, screen: MatLike, screenshot_time: float) -> bool:
        """
        识别画面是否有闪光
        :param screen:
        :param screenshot_time:
        :return:
        """
        if not self._check_dodge_flash_lock.acquire(blocking=False):
            return False

        try:
            result = self._dodge_model.run(screen)
            with_flash: bool = False
            if result.class_idx == 1:
                e = YoloStateEventEnum.DODGE_RED.value
                log.info(e)
                self.ctx.dispatch_event(e, screenshot_time)
                with_flash = True
            elif result.class_idx == 2:
                e = YoloStateEventEnum.DODGE_YELLOW.value
                log.info(e)
                self.ctx.dispatch_event(e, screenshot_time)
                with_flash = True

            return with_flash
        except Exception:
            log.error('识别画面闪光失败', exc_info=True)
        finally:
            self._check_dodge_flash_lock.release()
