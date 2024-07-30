from concurrent.futures import ThreadPoolExecutor, Future

from threading import Lock
from typing import Optional, List

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.utils import thread_utils

_od_op_task_executor = ThreadPoolExecutor(thread_name_prefix='_od_op_task_executor', max_workers=4)


class OperationTask:

    def __init__(self, op_list: List[AtomicOp]):
        """
        包含一串指令的任务
        :param op_list:
        """
        self.op_list: List[AtomicOp] = op_list
        self._running: bool = False
        self._current_op: Optional[AtomicOp] = None  # 当前执行的指令
        self._async_ops: List[AtomicOp] = []  # 执行过异步操作
        self._op_lock: Lock = Lock()  # 操作锁 用于保证stop里的一定是最后执行的op

    def run_async(self) -> Future:
        """
        异步执行
        :return:
        """
        self._running = True
        future: Future = _od_op_task_executor.submit(self._run)
        future.add_done_callback(thread_utils.handle_future_result)
        return future

    def _run(self) -> None:
        """
        执行
        :return:
        """
        for op in self.op_list:
            with self._op_lock:
                self._current_op = op
                self._async_ops.append(op)
                if not self._running:
                    break
            op.execute()
            with self._op_lock:
                self._current_op = None

    def stop(self) -> None:
        """
        停止运行
        :return:
        """
        with self._op_lock:
            self._running = False
            if self._current_op is not None:
                self._current_op.stop()
            for op in self._async_ops:
                op.stop()
