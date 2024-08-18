import time
from concurrent.futures import ThreadPoolExecutor, Future

import librosa
import numpy as np
import os
import threading
from cv2.typing import MatLike
from enum import Enum
from scipy.signal import correlate
from sklearn.preprocessing import scale
from typing import Optional, List, Union

from one_dragon.base.conditional_operation.state_event import StateEvent
from one_dragon.utils import cal_utils, yolo_config_utils
from one_dragon.utils import thread_utils, os_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.yolo.flash_classifier import FlashClassifier

# 创建一个线程池执行器，用于异步执行任务
_dodge_check_executor = ThreadPoolExecutor(thread_name_prefix='od_yolo_check', max_workers=16)


class AudioRecorder:
    """
    音频录制类，用于录制和处理音频数据。
    """

    def __init__(self):
        self.running: bool = False  # 标记录制是否正在运行
        self._run_lock = threading.Lock()  # 用于线程安全的锁

        self._sample_rate = 32000  # 采样率
        self._used_channel = 2  # 使用的音频通道数
        self._sample_len = 0.01  # 每次采样的长度（秒）
        self._chunk_size = int(self._sample_rate * self._sample_len)  # 每个音频块的大小

        self.latest_audio = np.empty(shape=(0,), dtype=np.float64)  # 存储最新的音频数据
        self._update_audio_lock = threading.Lock()

    def start_running_async(self, interval: float = 0.01) -> None:
        """
        异步启动音频录制。
        :param interval: 录制间隔时间
        """
        with self._run_lock:
            if self.running:
                return

            self.running = True

        self.latest_audio = np.zeros(int(self._sample_rate // 2))  # 初始化音频数据缓冲区，长度为0.5秒
        future = _dodge_check_executor.submit(self._record_loop)
        future.add_done_callback(thread_utils.handle_future_result)

    def _record_loop(self) -> None:
        """
        音频录制循环，持续录制音频数据。
        """
        import soundcard as sc
        _mic = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
        _recorder = _mic.recorder(samplerate=self._sample_rate, channels=self._used_channel)

        with _recorder as audio_recorder:
            while self.running:
                stream_data = audio_recorder.record(numframes=self._chunk_size)
                if self._used_channel > 1:
                    stream_data = librosa.to_mono(stream_data.T)
                else:
                    stream_data = stream_data.T

                with self._update_audio_lock:
                    # 更新 latest_audio
                    self.latest_audio[:-len(stream_data)] = self.latest_audio[len(stream_data):]
                    self.latest_audio[-len(stream_data):] = stream_data

    def stop_running(self) -> None:
        """
        停止音频录制。
        """
        self.running = False

    def clear_audio(self) -> None:
        """
        清楚当前录音
        """
        with self._update_audio_lock:
            self.latest_audio = np.zeros(int(self._sample_rate // 2))


class YoloStateEventEnum(Enum):
    """
    YOLO状态事件枚举类，定义不同的闪避识别事件。
    """
    DODGE_YELLOW = '闪避识别-黄光'
    DODGE_RED = '闪避识别-红光'
    DODGE_AUDIO = '闪避识别-声音'


class BattleDodgeContext:
    """
    战斗闪避上下文类，用于管理和处理闪避识别相关的逻辑。
    """

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx  # 上下文对象
        self._flash_model: Optional[FlashClassifier] = None  # 闪避分类器
        self._audio_recorder: AudioRecorder = AudioRecorder()  # 音频录制器
        self._audio_template: Optional[np.ndarray] = None  # 音频模板

        # 识别锁，保证每种类型只有一个实例在进行识别
        self._check_dodge_flash_lock = threading.Lock()
        self._check_audio_lock = threading.Lock()

        # 识别间隔
        self._check_dodge_interval: Union[float, List[float]] = 0
        self._check_audio_interval: float = 0.02

        # 上一次识别的时间
        self._last_check_dodge_time: float = 0
        self._last_check_audio_time: float = 0

        # 音频事件去重时间间隔
        self._audio_event_interval: float = 0.1
        self._last_audio_event_time: float = 0

    def init_context(self,
                     use_gpu: bool = True,
                     check_dodge_interval: Union[float, List[float]] = 0,
                     audio_recorder_interval: float = 0.01,
                     check_audio_interval: float = 0.02
                     ) -> None:
        """
        初始化上下文，在运行前调用。
        :param use_gpu: 是否使用GPU
        :param check_dodge_interval: 闪避识别间隔
        :param audio_recorder_interval: 音频录制间隔
        :param check_audio_interval: 音频识别间隔
        """
        if self._flash_model is None or self._flash_model.gpu != use_gpu:
            use_gh_proxy = self.ctx.env_config.is_ghproxy
            self._flash_model = FlashClassifier(
                model_name=self.ctx.yolo_config.flash_classifier,
                model_parent_dir_path=yolo_config_utils.get_model_category_dir('flash_classifier'),
                gh_proxy=use_gh_proxy,
                personal_proxy=None if use_gh_proxy else self.ctx.env_config.personal_proxy,
                gpu=use_gpu
            )

        # 识别间隔
        self._check_dodge_interval = check_dodge_interval
        self._check_audio_interval = check_audio_interval

        # 上一次识别的时间
        self._last_check_dodge_time = 0
        self._last_check_audio_time = 0

        self._audio_recorder.start_running_async(audio_recorder_interval)

        # 异步加载音频模板
        _dodge_check_executor.submit(self.init_audio_template)

    def init_audio_template(self) -> None:
        """
        加载音频模板。
        """
        if self._audio_template is not None:
            return
        log.info('加载声音模板中')
        self._audio_template, _ = librosa.load(os.path.join(
            os_utils.get_path_under_work_dir('assets', 'template', 'dodge_audio'),
            'template_1.wav'
        ), sr=32000)
        log.info('加载声音模板完成')

    def check_screen(self, screen: MatLike, screenshot_time: float, sync: bool = False) -> None:
        """
        异步识别画面。
        :param screen: 屏幕截图
        :param screenshot_time: 截图时间
        :param sync: 是否同步执行
        """
        future_list: List[Future] = []
        audio_future = _dodge_check_executor.submit(self.check_dodge_audio, screenshot_time)
        future_list.append(audio_future)
        future_list.append(_dodge_check_executor.submit(self.check_dodge_flash, screen, screenshot_time, audio_future))

        for future in future_list:
            future.add_done_callback(thread_utils.handle_future_result)

        if sync:
            for future in future_list:
                future.result()

    def check_dodge_flash(self, screen: MatLike, screenshot_time: float, audio_future: Optional[Future[bool]] = None) -> bool:
        """
        识别画面是否有闪光。
        :param screen: 屏幕截图
        :param screenshot_time: 截图时间
        :param audio_future: 音频识别结果的Future对象
        :return: 是否识别到闪光
        """
        if not self._check_dodge_flash_lock.acquire(blocking=False):
            return False

        try:
            if screenshot_time - self._last_check_dodge_time < cal_utils.random_in_range(self._check_dodge_interval):
                # 还没有达到识别间隔
                return False

            self._last_check_dodge_time = screenshot_time

            result = self._flash_model.run(screen)
            with_flash: bool = False
            if result.class_idx == 1:
                e = YoloStateEventEnum.DODGE_RED.value
                self.ctx.dispatch_event(e, StateEvent(screenshot_time))
                with_flash = True
            elif result.class_idx == 2:
                e = YoloStateEventEnum.DODGE_YELLOW.value
                self.ctx.dispatch_event(e, StateEvent(screenshot_time))
                with_flash = True
            elif audio_future is not None:
                audio_result = audio_future.result()
                if audio_result:
                    e = YoloStateEventEnum.DODGE_AUDIO.value
                    self.ctx.dispatch_event(e, StateEvent(screenshot_time))
                    with_flash = True

            return with_flash
        except Exception:
            log.error('识别画面闪光失败', exc_info=True)
        finally:
            self._check_dodge_flash_lock.release()

    def check_dodge_audio(self, screenshot_time: float) -> bool:
        """
        识别音频是否有闪避提示。
        :param screenshot_time: 截图时间
        :return: 是否识别到音频提示
        """
        if not self._check_audio_lock.acquire(blocking=False):
            return False

        try:
            if screenshot_time - self._last_check_audio_time < cal_utils.random_in_range(self._check_audio_interval):
                # 还没有达到识别间隔
                return False
            if self._audio_template is None:
                return False
            self._last_check_audio_time = screenshot_time

            corr = self.get_max_corr(self._audio_template, self._audio_recorder.latest_audio)
            log.debug('声音相似度 %.2f' % corr)

            # 事件去重逻辑
            if corr > 0.1:
                self._last_audio_event_time = screenshot_time
                self._audio_recorder.clear_audio()
                return True

            return False
        except Exception:
            log.error('识别画面闪光失败', exc_info=True)
        finally:
            self._check_audio_lock.release()

    @staticmethod
    def get_max_corr(x: np.ndarray, y: np.ndarray):
        """
        计算两个音频信号的最大相关性。
        :param x: 音频信号x
        :param y: 音频信号y
        :return: 最大相关性系数
        """
        # 标准化
        wx = scale(x, with_mean=False)
        wy = scale(y, with_mean=False)

        # 计算NCC
        if wx.shape[0] > wy.shape[0]:
            correlation = correlate(wx, wy, mode='same', method='fft') / wx.shape[0]
        else:
            correlation = correlate(wy, wx, mode='same', method='fft') / wy.shape[0]

        max_corr = np.max(correlation)

        return max_corr

    def stop_context(self) -> None:
        """
        停止上下文，停止音频录制。
        """
        self._audio_recorder.stop_running()

    def resume_context(self) -> None:
        """
        恢复上下文，重新启动音频录制。
        """
        self._audio_recorder.start_running_async(self._check_audio_interval)


def __debug():
    """
    调试函数，用于测试战斗闪避上下文的功能。
    """
    ctx = ZContext()
    ctx.init_by_config()

    from one_dragon.utils import debug_utils
    img = debug_utils.get_debug_image('flash')

    ctx.battle_dodge.init_audio_template()
    ctx.battle_dodge._audio_recorder.start_running_async(0.01)
    while True:
        ctx.battle_dodge.check_dodge_audio(time.time())
        time.sleep(0.02)
    print(ctx.battle_dodge.get_max_corr(ctx.battle_dodge._audio_template, ctx.battle_dodge._audio_template))


if __name__ == '__main__':
    __debug()