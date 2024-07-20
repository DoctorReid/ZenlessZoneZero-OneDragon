class AtomicOp:

    def __init__(self, op_name: str):
        """
        一个原子指令，没有任何判断，执行后上抛事件
        :param op_name: 指令名称
        """
        self.op_name: str = op_name

    def execute(self):
        """
        执行指令 必要时上抛状态事件
        """
        pass

    def dispose(self) -> None:
        """
        销毁时 解出事件监听
        :return:
        """
        pass
