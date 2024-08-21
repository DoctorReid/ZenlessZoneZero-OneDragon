from typing import Optional, List


class OperationDef:

    def __init__(self,
                 op_name: Optional[str] = None,
                 data: Optional[List[str]] = None,
                 operation_template: Optional[str] = None,

                 # 通用
                 pre_delay: float = 0,
                 post_delay: float = 0,

                 # 按键特有的属性
                 way: Optional[str] = None,
                 press: Optional[float] = None,
                 repeat: int = 1,

                 # 等待秒数
                 seconds: float = 0,

                 # 状态
                 state: Optional[str] = None,
                 value: Optional[int] = None,
                 add: Optional[int] = None,
                 ):
        self.op_name: str = op_name
        self.data: List[str] = data
        self.operation_template: str = operation_template

        self.pre_delay: float = pre_delay  # 前延迟
        self.post_delay: float = post_delay  # 后延迟

        self.btn_way: str = way  # 按键方式
        self.btn_press: float = press  # 按键时间
        self.btn_repeat_times: int = repeat  # 重复次数

        self.wait_seconds: float = seconds  # 等待秒数

        self.state_name: str = state  # 状态名称
        self.state_seconds: float = seconds  # 状态处罚时间偏移量
        self.state_value: int = value  # 设置的状态值
        self.state_value_add: int = add  # 设置的状态值偏移量 state_value存在时不生效
