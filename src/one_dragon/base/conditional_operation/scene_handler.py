from typing import List

from one_dragon.base.conditional_operation.state_handler import StateHandler


class SceneHandler:

    def __init__(self, interval_seconds: float, state_handlers: List[StateHandler]):
        self.interval_seconds: float = interval_seconds
        self.state_handlers: List[StateHandler] = state_handlers
        self.last_trigger_time: float = 0

    def execute(self, now: float) -> None:
        """
        按优先级判断状态 找到需要执行的执行并执行
        :param now:
        :return:
        """
        if now - self.last_trigger_time <= self.interval_seconds:
            return
        self.last_trigger_time = now
        for sh in self.state_handlers:
            if sh.check_and_run(now):
                return

    def stop_running(self) -> None:
        """
        停止运行
        :return:
        """
        for sh in self.state_handlers:
            sh.stop_running()

    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        if self.state_handlers is not None:
            for handler in self.state_handlers:
                handler.dispose()
