import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import librosa
import numpy as np
import os
import soundcard as sc
import threading

from one_dragon.utils import thread_utils, os_utils
from one_dragon.utils.log_utils import log

from scipy.signal import correlate
from sklearn.preprocessing import scale

_sound_record_executor = ThreadPoolExecutor(thread_name_prefix='od_sound_recorder', max_workers=2)


class AudioRecorder:

    def __init__(self):
        self.running: bool = False
        self._run_lock = threading.Lock()

        self._sample_rate = 32000  # 采样率
        self._used_channel = 2
        self._mic = sc.default_microphone()

        self.latest_audio = np.zeros(self._sample_rate)  # 1秒的音频帧数

    def start_running_async(self, interval: float = 0.01) -> None:
        with self._run_lock:
            if self.running:
                return

            self.running = True

        self.latest_audio = np.zeros(self._sample_rate)
        future = _sound_record_executor.submit(self._record_loop, interval)
        future.add_done_callback(thread_utils.handle_future_result)

    def _record_loop(self, interval: float = 0.01) -> None:
        window_size = int(self._sample_rate * interval)
        while self.running:
            recording = self._mic.record(numframes=window_size, samplerate=self._sample_rate, channels=self._used_channel)
            mono = librosa.to_mono(recording)
            latest_audio = np.roll(self.latest_audio, -len(mono))
            latest_audio[-len(mono):] = mono
            self.latest_audio = latest_audio

    def stop_running(self) -> None:
        self.running = False


class BattleAudioContext:

    def __init__(self):
        self._recorder: AudioRecorder = AudioRecorder()
        self._template = None

        # 识别锁 保证每种类型只有1实例在进行识别
        self._check_audio_lock = threading.Lock()

        # 识别间隔
        self._check_audio_interval: float = 0.02

        # 上一次识别的时间
        self._last_check_audio_time: float = 0

    def init_context(self,
                     recorder_interval: float = 0.01,
                     check_audio_interval: float = 0.02
                     ) -> None:
        log.info('加载声音模板中')
        self._template, _ = librosa.load(os.path.join(
            os_utils.get_path_under_work_dir('assets', 'template', 'dodge_audio'),
            'template_1.wav'
        ), sr=32000)
        log.info('加载声音模板完成')

        # 识别间隔
        self._check_audio_interval = check_audio_interval

        # 上一次识别的时间
        self._last_check_audio_time = 0

        self._recorder.start_running_async(recorder_interval)

    def stop_context(self) -> None:
        self._recorder.stop_running()




if __name__ == '__main__':
    ctx = BattleAudioContext()
    # ctx.init_context()
    # cv2.waitKey(0)
    t1 = time.time()
    ctx.get_max_corr(ctx.input, ctx.input)
    t2 = time.time()
    print(t2 - t1)
    ctx.match_2(ctx.input, ctx.input)
    t3 = time.time()
    print(t3 - t2)
    pass