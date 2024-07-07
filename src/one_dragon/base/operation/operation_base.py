from typing import Optional, Any


class OperationResult:

    def __init__(self, success: bool, status: Optional[str] = None, data: Any = None):
        """
        指令最后的结果
        :param success: 指令执行结果
        :param status: 附带状态
        """
        self.success: bool = success
        """指令执行结果 - 框架固定"""
        self.status: str = status
        """结果状态 - 每个指令独特"""
        self.data: Any = data
        """返回数据"""


class OperationBase:

    def __init__(self):
        """
        一个基础指令框架
        """
        pass

    def execute(self) -> OperationResult:
        """
        由子类实现 完成这个指令的动作
        :return:
        """
        return self.op_success()

    @staticmethod
    def op_success(status: str = None, data: Any = None) -> OperationResult:
        """
        整个指令执行成功
        :param status: 附带状态
        :param data: 返回数据
        :return:
        """
        return OperationResult(success=True, status=status, data=data)

    @staticmethod
    def op_fail(status: str = None, data: Any = None) -> OperationResult:
        """
        整个指令执行失败
        :param status: 附带状态
        :param data: 返回数据
        :return:
        """
        return OperationResult(success=False, status=status, data=data)