import time

import inspect
from cv2.typing import MatLike
from typing import Optional, ClassVar, Callable, List, Any

from one_dragon.base.operation.one_dragon_context import OneDragonContext, ContextRunningStateEventEnum
from one_dragon.base.operation.operation_base import OperationBase, OperationResult
from one_dragon.base.operation.operation_edge import OperationEdge, OperationEdgeDesc
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.base.operation.operation_round_result import OperationRoundResultEnum, OperationRoundResult
from one_dragon.base.screen import screen_utils
from one_dragon.base.screen.screen_utils import OcrClickResultEnum, FindAreaResultEnum
from one_dragon.utils import debug_utils
from one_dragon.utils.i18_utils import coalesce_gt
from one_dragon.utils.log_utils import log


class Operation(OperationBase):
    """
    指令 本身可暂停 但不由自身恢复
    """
    STATUS_TIMEOUT: ClassVar[str] = '执行超时'

    def __init__(self, ctx: OneDragonContext,
                 node_max_retry_times: int = 3,
                 op_name: str = '',
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 need_check_game_win: bool = True,
                 op_to_enter_game:  Optional[OperationBase] = None
                 ):
        OperationBase.__init__(self)

        self.op_name: str = op_name
        """指令名称"""

        self.node_max_retry_times: int = node_max_retry_times
        """每个节点可以重试的次数"""

        self.ctx: OneDragonContext = ctx
        """上下文"""

        self.timeout_seconds: float = timeout_seconds
        """指令超时时间"""

        self.op_callback: Optional[Callable[[OperationResult], None]] = op_callback
        """指令结束后的回调"""

        self.need_check_game_win: bool = need_check_game_win
        """是否检测游戏窗口"""

        self.op_to_enter_game: OperationBase = op_to_enter_game
        """用于打开游戏的指令"""

    def _init_before_execute(self):
        """
        执行前的初始化
        :return:
        """
        now = time.time()

        self.node_retry_times: int = 0
        """当前节点的重试次数"""

        self.operation_start_time: float = now
        """指令开始执行的时间"""

        self.pause_start_time: float = now
        """本次暂停开始的时间 on_pause时填入"""

        self.current_pause_time: float = 0
        """本次暂停的总时间 on_resume时填入"""

        self.pause_total_time: float = 0
        """暂停的总时间"""

        self.round_start_time: float = 0
        """本轮指令的开始时间"""

        self.last_screenshot: Optional[MatLike] = None
        """上一次的截图 用于出错时保存"""

        self.param_start_node: OperationNode = None
        """入参的开始节点 当网络存在环时 需要自己指定"""

        self._add_edge_list: List[OperationEdge] = []
        """调用方法添加的边"""

        self._init_network()
        self._current_node_start_time = now
        """当前节点开始时间"""

        self.ctx.unlisten_all_event(self)
        self.ctx.listen_event(ContextRunningStateEventEnum.PAUSE_RUNNING.value, self._on_pause)
        self.ctx.listen_event(ContextRunningStateEventEnum.RESUME_RUNNING.value, self._on_resume)

        self.handle_init()

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        pass

    def _add_edges_and_nodes_by_annotation(self) -> None:
        """
        初始化前 读取类方法的标注 自动添加边和节点
        :return:
        """
        node_name_map: dict[str, OperationNode] = {}
        edge_desc_list: List[OperationEdgeDesc] = []

        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            node: OperationNode = method.__annotations__.get('operation_node_annotation')
            if node is not None:
                node_name_map[node.cn] = node
            else:  # 不是节点的话 一定没有边
                continue
            if node.is_start_node:
                self.param_start_node = node
            edges: List[OperationEdgeDesc] = method.__annotations__.get('operation_edge_annotation')
            if edges is not None:
                for edge in edges:
                    edge.node_to_name = node.cn
                    edge_desc_list.append(edge)

        for edge_desc in edge_desc_list:
            node_from = node_name_map.get(edge_desc.node_from_name, None)
            if node_from is None:
                raise ValueError('找不到节点 %s' % edge_desc.node_from_name)
            node_to = node_name_map.get(edge_desc.node_to_name, None)
            if node_to is None:
                raise ValueError('找不到节点 %s' % edge_desc.node_to_name)
            self.add_edge(node_from, node_to,
                          success=edge_desc.success,
                          status=edge_desc.status,
                          ignore_status=edge_desc.ignore_status)

    def _init_edge_list(self) -> None:
        """
        初始化边列表
        :return:
        """
        self.edge_list: List[OperationEdge] = []
        """合并的边列表"""

        if len(self._add_edge_list) > 0:
            for edge in self._add_edge_list:
                self.edge_list.append(edge)

    def add_edge(self, node_from: OperationNode, node_to: OperationNode,
                 success: bool = True, status: Optional[str] = None, ignore_status: bool = True):
        """
        添加一条边
        :param node_from:
        :param node_to:
        :param success:
        :param status:
        :param ignore_status:
        :return:
        """
        self._add_edge_list.append(OperationEdge(node_from, node_to,
                                                 success=success, status=status, ignore_status=ignore_status))

    def _init_network(self) -> None:
        """
        进行节点网络的初始化
        :return:
        """
        self._add_edges_and_nodes_by_annotation()
        self.add_edges_and_nodes()
        self._init_edge_list()

        self._node_edges_map: dict[str, List[OperationEdge]] = {}
        """下一个节点的集合"""

        self._node_map: dict[str, OperationNode] = {}
        """节点"""

        self._current_node_start_time: Optional[float] = None
        """当前节点的开始运行时间"""

        op_in_map: dict[str, int] = {}  # 入度

        for edge in self.edge_list:
            from_id = edge.node_from.cn
            if from_id not in self._node_edges_map:
                self._node_edges_map[from_id] = []
            self._node_edges_map[from_id].append(edge)

            to_id = edge.node_to.cn
            if to_id not in op_in_map:
                op_in_map[to_id] = 0
            op_in_map[to_id] = op_in_map[to_id] + 1

            self._node_map[from_id] = edge.node_from
            self._node_map[to_id] = edge.node_to

        if len(self.edge_list) == 0 and self.param_start_node is not None:  # 只有一个节点的情况
            self._node_map[self.param_start_node.cn] = self.param_start_node

        start_node: Optional[OperationNode] = None
        if self.param_start_node is None:  # 没有指定开始节点时 自动判断
            # 找出入度为0的开始点
            for edge in self.edge_list:
                from_id = edge.node_from.cn
                if from_id not in op_in_map or op_in_map[from_id] == 0:
                    if start_node is not None and start_node.cn != from_id:
                        start_node = None
                        break
                    start_node = self._node_map[from_id]
        else:
            start_node = self.param_start_node

        if self.need_check_game_win and start_node is not None:
            check_game_window = OperationNode('检测游戏窗口', self.check_game_window)
            self._node_map[check_game_window.cn] = check_game_window

            open_and_enter_game = OperationNode('打开并进入游戏', self.open_and_enter_game)
            self._node_map[open_and_enter_game.cn] = open_and_enter_game

            no_game_edge = OperationEdge(check_game_window, open_and_enter_game, success=False)
            with_game_edge = OperationEdge(check_game_window, start_node)
            enter_game_edge = OperationEdge(open_and_enter_game, start_node)

            self._node_edges_map[check_game_window.cn] = [no_game_edge, with_game_edge]
            self._node_edges_map[open_and_enter_game.cn] = [enter_game_edge]

            start_node = check_game_window

        self._start_node: OperationNode = start_node
        """其实节点 初始化后才会有"""

        self._current_node: OperationNode = start_node
        """当前执行的节点"""

    def check_game_window(self) -> OperationRoundResult:
        """
        检测游戏
        :return:
        """
        if self.ctx.is_game_window_ready:
            return self.round_success()
        else:
            return self.round_fail('未打开游戏窗口 %s' % self.ctx.controller.game_win.win_title)

    def open_and_enter_game(self) -> OperationRoundResult:
        """
        打开并进入游戏
        :return:
        """
        if self.op_to_enter_game is None:
            return self.round_fail('未提供打开游戏方式')
        else:
            return self.round_by_op(self.op_to_enter_game.execute())

    def handle_init(self):
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def execute(self) -> OperationResult:
        """
        循环执行指令直到完成为止
        """
        try:
            self._init_before_execute()
        except Exception:
            log.error('初始化失败', exc_info=True)
            return self.op_fail('初始化失败')

        op_result: Optional[OperationResult] = None
        while True:
            self.round_start_time = time.time()
            if self.timeout_seconds != -1 and self.operation_usage_time >= self.timeout_seconds:
                op_result = self.op_fail(Operation.STATUS_TIMEOUT)
                break
            if self.ctx.is_context_stop:
                op_result = self.op_fail('人工结束')
                break
            elif self.ctx.is_context_pause:
                time.sleep(1)
                continue

            try:
                round_result: OperationRoundResult = self._execute_one_round()
                if self.ctx.is_context_pause:  # 有可能触发暂停的时候仍在执行指令 执行完成后 再次触发暂停回调 保证操作的暂停回调真正生效
                    self._on_pause()
            except Exception as e:
                round_result: OperationRoundResult = self.round_retry('异常')
                if self.last_screenshot is not None:
                    file_name = self.save_screenshot()
                    log.error('%s 执行出错 相关截图保存至 %s', self.display_name, file_name, exc_info=True)
                else:
                    log.error('%s 执行出错', self.display_name, exc_info=True)

            # 重试或者等待的
            if round_result.result == OperationRoundResultEnum.RETRY:
                self.node_retry_times += 1
                if self.node_retry_times <= self.node_max_retry_times:
                    continue
                else:
                    round_result.result = OperationRoundResultEnum.FAIL
            elif round_result.result == OperationRoundResultEnum.WAIT:
                continue

            # 成功或者失败的 找下一个节点
            next_node = self._get_next_node(round_result)
            if next_node is None:  # 没有下一个节点了 当前返回什么就是什么
                if round_result.result == OperationRoundResultEnum.SUCCESS:
                    op_result = self.op_success(round_result.status, round_result.data)
                    break
                elif round_result.result == OperationRoundResultEnum.FAIL:
                    op_result = self.op_fail(round_result.status, round_result.data)
                    break
                else:
                    log.error('%s 执行返回结果错误 %s', self.display_name, op_result)
                    op_result = self.op_fail(round_result.status)
                    break
            else:  # 继续下一个节点
                self._current_node = next_node
                self.node_retry_times = 0  # 每个节点都可以重试
                self._current_node_start_time = time.time()  # 每个节点单独计算耗时
                continue

        self._after_operation_done(op_result)
        return op_result

    def _execute_one_round(self) -> OperationRoundResult:
        if self._current_node is None:
            return self.round_fail('当前节点为空')

        if self._current_node.timeout_seconds is not None \
                and self._current_node_start_time is not None \
                and time.time() - self._current_node_start_time > self._current_node.timeout_seconds:
            return self.round_fail(Operation.STATUS_TIMEOUT)

        if self._current_node.func is not None:
            current_op = self._current_node.func
            current_round_result: OperationRoundResult = current_op()
        elif self._current_node.op_method is not None:
            current_round_result: OperationRoundResult = self._current_node.op_method(self)
        elif self._current_node.op is not None:
            op_result = self._current_node.op.execute()
            current_round_result = self.round_by_op(op_result,
                                                    retry_on_fail=self._current_node.retry_on_op_fail,
                                                    wait=self._current_node.wait_after_op)
        else:
            return self.round_fail('节点处理函数和指令都没有设置')

        if current_round_result is None:
            log.error(f'节点 {self._current_node.cn} 返回状态为None')

        log.info('%s 节点 %s 返回状态 %s', self.display_name, self._current_node.cn,
                 coalesce_gt(current_round_result.status, current_round_result.status_display, model='ui'))

        return current_round_result

    def _get_next_node(self, current_round_result: OperationRoundResult):
        """
        根据当前轮的结果 找到下一个节点
        :param current_round_result:
        :return:
        """
        if self._current_node is None:
            return None
        edges = self._node_edges_map.get(self._current_node.cn)
        if edges is None or len(edges) == 0:  # 没有下一个节点了
            return None

        next_node_id: Optional[str] = None
        final_next_node_id: Optional[str] = None  # 兜底指令
        for edge in edges:
            if edge.success != (current_round_result.result == OperationRoundResultEnum.SUCCESS):
                continue

            if edge.ignore_status:
                final_next_node_id = edge.node_to.cn

            if edge.status is None and current_round_result.status is None:
                next_node_id = edge.node_to.cn
                break
            elif edge.status is None or current_round_result.status is None:
                continue
            elif edge.status == current_round_result.status:
                next_node_id = edge.node_to.cn
                break

        if next_node_id is not None:
            return self._node_map[next_node_id]
        elif final_next_node_id is not None:
            return self._node_map[final_next_node_id]
        else:
            return None

    def _on_pause(self, e=None):
        """
        暂停运行时触发的回调
        由于触发时，操作有机会仍在执行逻辑，因此_execute_one_round后会判断一次暂停状态触发on_pause
        子类需要保证多次触发不会有问题
        :return:
        """
        if not self.ctx.is_context_pause:
            return
        self.current_pause_time = 0
        self.pause_start_time = time.time()
        self.handle_pause()

    def handle_pause(self) -> None:
        """
        暂停后的处理 由子类实现
        :return:
        """
        pass

    def _on_resume(self, e=None):
        """
        脚本恢复运行时的回调
        :param e:
        :return:
        """
        if not self.ctx.is_context_running:
            return
        self.current_pause_time = time.time() - self.pause_start_time
        self.pause_total_time += self.current_pause_time
        self._current_node_start_time += self.current_pause_time
        self.handle_resume()

    def handle_resume(self) -> None:
        """
        恢复运行后的处理 由子类实现
        :return:
        """
        pass

    @property
    def operation_usage_time(self) -> float:
        """
        获取指令的耗时
        :return:
        """
        return time.time() - self.operation_start_time - self.pause_total_time

    def screenshot(self):
        """
        包装一层截图 会在内存中保存上一张截图 方便出错时候保存
        :return:
        """
        screen = self.ctx.controller.screenshot()
        self.last_screenshot = screen
        return self.last_screenshot

    def save_screenshot(self) -> str:
        """
        保存上一次的截图 并对UID打码
        :return: 文件路径
        """
        if self.last_screenshot is None:
            return ''
        return debug_utils.save_debug_image(self.last_screenshot, prefix=self.__class__.__name__)

    @property
    def display_name(self) -> str:
        """
        用于展示的名称
        :return:
        """
        return '指令[ %s ]' % self.op_name

    def _after_operation_done(self, result: OperationResult):
        """
        动作结算后的处理
        :param result:
        :return:
        """
        self.ctx.unlisten_all_event(self)
        if result.success:
            log.info('%s 执行成功 返回状态 %s', self.display_name, coalesce_gt(result.status, '成功', model='ui'))
        else:
            log.error('%s 执行失败 返回状态 %s', self.display_name, coalesce_gt(result.status, '失败', model='ui'))

        if self.op_callback is not None:
            self.op_callback(result)

    def round_success(self, status: str = None, data: Any = None,
                      wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationRoundResult(result=OperationRoundResultEnum.SUCCESS, status=status, data=data)

    def round_wait(self, status: str = None, data: Any = None,
                   wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationRoundResult(result=OperationRoundResultEnum.WAIT, status=status, data=data)

    def round_retry(self, status: str = None, data: Any = None,
                    wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationRoundResult(result=OperationRoundResultEnum.RETRY, status=status, data=data)

    def round_fail(self, status: str = None, data: Any = None,
                   wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationRoundResult:
        """
        单轮成功 - 即整个指令成功
        :param status: 附带状态
        :param data: 返回数据
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        self._after_round_wait(wait=wait, wait_round_time=wait_round_time)
        return OperationRoundResult(result=OperationRoundResultEnum.FAIL, status=status, data=data)

    def _after_round_wait(self, wait: Optional[float] = None, wait_round_time: Optional[float] = None):
        """
        每轮指令后进行的等待
        :param wait: 等待秒数
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        if wait is not None and wait > 0:
            time.sleep(wait)
        elif wait_round_time is not None and wait_round_time > 0:
            to_wait = wait_round_time - (time.time() - self.round_start_time)
            if to_wait > 0:
                time.sleep(to_wait)

    def round_by_op(self, op_result: OperationResult, retry_on_fail: bool = False,
                    wait: Optional[float] = None, wait_round_time: Optional[float] = None) -> OperationRoundResult:
        """
        根据一个指令的结果获取当前轮的结果
        :param op_result: 指令结果
        :param retry_on_fail: 失败的时候是否重试
        :param wait: 等待时间
        :param wait_round_time: 等待当前轮的运行时间到达这个时间时再结束 有wait时不生效
        :return:
        """
        if op_result.success:
            return self.round_success(status=op_result.status, data=op_result.data, wait=wait,
                                      wait_round_time=wait_round_time)
        elif retry_on_fail:
            return self.round_retry(status=op_result.status, data=op_result.data, wait=wait,
                                    wait_round_time=wait_round_time)
        else:
            return self.round_fail(status=op_result.status, data=op_result.data, wait=wait,
                                   wait_round_time=wait_round_time)

    def round_fail_by_op(self, op_result: OperationResult) -> OperationRoundResult:
        return self.round_fail(status=op_result.status, data=op_result.data)

    def round_by_find_and_click_area(self, screen: MatLike, screen_name: str, area_name: str,
                                     success_wait: Optional[float] = None, success_wait_round: Optional[float] = None,
                                     retry_wait: Optional[float] = None, retry_wait_round: Optional[float] = None,
                                     ) -> OperationRoundResult:
        """
        是否能找到目标区域 并进行点击
        :param screen: 屏幕截图
        :param screen_name: 画面名称
        :param area_name: 区域名称
        :param success_wait: 成功后等待的秒数
        :param success_wait_round: 成功后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :param retry_wait: 失败后等待的秒数
        :param retry_wait_round: 失败后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :return:
        """
        click = screen_utils.find_and_click_area(ctx=self.ctx, screen=screen, screen_name=screen_name, area_name=area_name)
        if click == OcrClickResultEnum.OCR_CLICK_SUCCESS:
            return self.round_success(status=area_name, wait=success_wait, wait_round_time=success_wait_round)
        elif click == OcrClickResultEnum.OCR_CLICK_NOT_FOUND:
            return self.round_retry(status=f'未找到{area_name}', wait=retry_wait, wait_round_time=retry_wait_round)
        elif click == OcrClickResultEnum.OCR_CLICK_FAIL:
            return self.round_retry(status=f'点击{area_name}失败', wait=retry_wait, wait_round_time=retry_wait_round)
        elif click == OcrClickResultEnum.AREA_NO_CONFIG:
            return self.round_fail(status=f'区域{area_name}未配置')
        else:
            return self.round_retry(status='未知状态', wait=retry_wait, wait_round_time=retry_wait_round)

    def round_by_find_area(self, screen: MatLike, screen_name: str, area_name: str,
                           success_wait: Optional[float] = None, success_wait_round: Optional[float] = None,
                           retry_wait: Optional[float] = None, retry_wait_round: Optional[float] = None,
                           ) -> OperationRoundResult:
        """
        是否能找到目标区域
        :param screen: 屏幕截图
        :param screen_name: 画面名称
        :param area_name: 区域名称
        :param success_wait: 成功后等待的秒数
        :param success_wait_round: 成功后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :param retry_wait: 失败后等待的秒数
        :param retry_wait_round: 失败后等待当前轮的运行时间到达这个时间时再结束 优先success_wait
        :return:
        """
        result = screen_utils.find_area(ctx=self.ctx, screen=screen, screen_name=screen_name, area_name=area_name)
        if result == FindAreaResultEnum.AREA_NO_CONFIG:
            return self.round_fail(status=f'区域{area_name}未配置')
        elif result == FindAreaResultEnum.TRUE:
            return self.round_success(wait=success_wait, wait_round_time=success_wait_round)
        else:
            return self.round_retry(wait=retry_wait, wait_round_time=retry_wait_round)

    def click_area(self, screen_name: str, area_name: str) -> bool:
        """
        无脑点击某个区域一次
        :param screen_name:
        :param area_name:
        :return: 是否点击成功
        """
        area = self.ctx.screen_loader.get_area(screen_name, area_name)
        if area is None:
            return False
        return self.ctx.controller.click(pos=area.center, pc_alt=area.pc_alt)

    def round_by_click_area(
            self, screen_name: str, area_name: str,
            success_wait: Optional[float] = None, success_wait_round: Optional[float] = None,
            retry_wait: Optional[float] = None, retry_wait_round: Optional[float] = None
    ) -> OperationRoundResult:
        if self.click_area(screen_name, area_name):
            return self.round_success(wait=success_wait, wait_round_time=success_wait_round)
        else:
            return self.round_retry(status=f'点击{area_name}失败', wait=retry_wait, wait_round_time=retry_wait_round)