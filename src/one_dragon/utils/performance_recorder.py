import time
import os
import yaml

from one_dragon.utils.log_utils import log


class PerformanceRecord:

    def __init__(self, id: str):
        self.id = id
        self.cnt = 0
        self.total = 0
        self.max = 0
        self.min = 999

    def add(self, t):
        self.cnt += 1
        self.total += t
        if t > self.max:
            self.max = t
        if t < self.min:
            self.min = t

    @property
    def avg(self):
        return self.total / self.cnt if self.cnt > 0 else 0

    def __repr__(self):
        return ('[%s] 次数: %d 平均耗时: %.6f 最高耗时: %.6f, 最低耗时: %.6f, 总耗时: %.6f' %
                (self.id, self.cnt, self.avg, self.max, self.min, self.total))


class PerformanceRecorder:

    def __init__(self):
        self.record_map = {}

    def record(self, id: str, t: float):
        """
        记录一个耗时
        :param id:
        :param t:
        :return:
        """
        if id not in self.record_map:
            self.record_map[id] = PerformanceRecord(id)

        self.record_map[id].add(t)

    def get_record(self, id: str):
        return self.record_map[id] if id in self.record_map else PerformanceRecord(id)


_recorder = PerformanceRecorder()


def get_recorder():
    return _recorder


def add_record(id: str, t: float):
    _recorder.record(id, t)


def record_performance(func):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        add_record(func.__name__, time.time() - t1)
        return result
    return wrapper


def get(id: str):
    return _recorder.get_record(id)


def log_all_performance():
    for v in _recorder.record_map.values():
        log.debug(str(v))

    # save_performance_record()


# def save_performance_record():
#     """
#     保存性能记录 用于辨别问题
#     :return:
#     """
#     path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'performance.txt')
#     data = {}
#     data['cpu_frequency'] = f"{psutil.cpu_freq().current}MHz"
#     data['cpu_count'] = psutil.cpu_count()
#     memory_info = psutil.virtual_memory()
#     data['memory_total'] = f"{memory_info.total / (1024.0 ** 3)} GB"
#     data['memory_used'] = f"{memory_info.used / (1024.0 ** 3)} GB"
#     for k, v in recorder.record_map.items():
#         data['time_%s' % k] = v.avg
#
#     with open(path, 'w', encoding='utf-8') as file:
#         yaml.dump(data, file)
