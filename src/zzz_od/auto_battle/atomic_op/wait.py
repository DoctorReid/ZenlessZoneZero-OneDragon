import time

from typing import ClassVar

from one_dragon.base.conditional_operation.atomic_op import AtomicOp


class AtomicWait(AtomicOp):

    OP_NAME: ClassVar[str] = '等待秒数'

    def __init__(self, wait_seconds: float):
        AtomicOp.__init__(self, op_name='%s %.2f' % (AtomicWait.OP_NAME, wait_seconds))
        self.wait_seconds: float = wait_seconds

    def execute(self):
        time.sleep(self.wait_seconds)
