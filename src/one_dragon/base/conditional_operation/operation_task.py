from concurrent.futures import ThreadPoolExecutor, Future

from threading import Lock
from typing import Optional, List

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.utils import thread_utils
from one_dragon.utils.log_utils import log

_od_op_task_executor = ThreadPoolExecutor(thread_name_prefix='_od_op_task_executor', max_workers=32)


class OperationTask:

    def __init__(self, is_trigger: bool, op_list: List[AtomicOp], priority: Optional[int] = None):
        """
        包含一串指令的任务
        :param op_list:
        """
        self.is_trigger: bool = is_trigger
        self.op_list: List[AtomicOp] = op_list
        self._running: bool = False
        self._current_op: Optional[AtomicOp] = None  # 当前执行的指令
        self._async_ops: List[AtomicOp] = []  # 执行过异步操作
        self._op_lock: Lock = Lock()  # 操作锁 用于保证stop里的一定是最后执行的op
        self.priority: Optional[int] = priority  # 优先级 只能被高等级的打断；为None时可以被随意打断

    def run_async(self) -> Future:
        """
        异步执行
        :return:
        """
        self._running = True
        future: Future = _od_op_task_executor.submit(self._run)
        future.add_done_callback(thread_utils.handle_future_result)
        return future

    def _run(self) -> bool:
        """
        执行
        :return: 是否完成所有指令了
        """
        for idx in range(len(self.op_list)):
            with self._op_lock:
                if not self._running:
                    # 被stop中断了 不继续后续的操作
                    break
                self._current_op = self.op_list[idx]
                if self._current_op.async_op:
                    self._async_ops.append(self._current_op)
                future: Future = _od_op_task_executor.submit(self._current_op.execute)

            try:
                future.result()
            except Exception:
                log.error('指令执行出错', exc_info=True)

            with self._op_lock:
                if not self._running:
                    # 被stop中断了 那么应该认为这个op没有执行完 不进行后续判断
                    break
                self._current_op = None
                if self._running and idx == len(self.op_list) - 1:
                    self._running = False
                    return True

        return False

    def stop(self) -> bool:
        """
        停止运行
        :return: 停止前是否已经完成所有指令了
        """
        with self._op_lock:
            if not self._running:
                # _run里面已经把op执行完了 就不需要额外的停止操作了
                self._current_op = None
                self._async_ops.clear()
                return True

            self._running = False
            if self._current_op is not None:
                self._current_op.stop()
                self._current_op = None
            for op in self._async_ops:
                op.stop()
            self._async_ops.clear()
            return False
