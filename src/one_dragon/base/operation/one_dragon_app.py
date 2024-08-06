from typing import List, Optional, ClassVar

from one_dragon.base.operation.application_base import Application
from one_dragon.base.operation.application_run_record import AppRunRecord
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.base.operation.operation_node import OperationNode
from one_dragon.utils.i18_utils import gt


class OneDragonApp(Application):

    STATUS_ALL_DONE: ClassVar[str] = '全部结束'
    STATUS_NEXT: ClassVar[str] = '下一个'

    def __init__(self, ctx: OneDragonContext, app_id: str,
                 app_list: List[Application]):
        Application.__init__(
            self,
            ctx, app_id,
            op_name=gt('一条龙', 'ui')
        )

        self.app_list: List[Application] = app_list
        self._to_run_app_list: List[Application] = []  # 需要执行的app列表 有序
        self._current_app_idx: int = 0  # 当前运行的app 下标

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_app = OperationNode('检测任务状态', self.check_app)
        run_app = OperationNode('运行任务', self.run_app)
        self.add_edge(check_app, run_app)
        self.add_edge(run_app, run_app, status=OneDragonApp.STATUS_NEXT)

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        for app in self.app_list:  # 运行一条龙时 各app不需要改变上下文
            app.init_context_before_start = False
            app.stop_context_after_stop = False

    def get_one_dragon_apps_in_order(self) -> List[Application]:
        """
        按运行顺序配置 返回需要在一条龙中运行的app
        :return:
        """
        all_apps = self.app_list
        app_orders = self.ctx.one_dragon_config.app_order

        result_list: List[Application] = []
        # 按顺序加入
        for app_order in app_orders:
            for app in all_apps:
                if app.app_id == app_order:
                    result_list.append(app)
                    break

        # 把没有在顺序里的加入
        for app in all_apps:
            if app.app_id not in app_orders:
                result_list.append(app)

        # 每次都更新配置
        new_app_orders = [app.app_id for app in result_list]
        self.ctx.one_dragon_config.app_order = new_app_orders

        return result_list

    def get_app(self, app_id: str) -> Optional[Application]:
        """
        获取应用
        :param app_id:
        :return:
        """
        for app in self.app_list:
            if app.app_id == app_id:
                return app

        return None

    def check_app(self) -> OperationRoundResult:
        """
        找出需要运行的app
        :return:
        """
        order_app_list = self.get_one_dragon_apps_in_order()

        self._to_run_app_list = []
        for app in order_app_list:
            if app.app_id not in self.ctx.one_dragon_config.app_run_list:
                continue
            if app.run_record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
                continue
            self._to_run_app_list.append(app)

        self._current_app_idx = 0

        return self.round_success()

    def run_app(self) -> OperationRoundResult:
        """
        运行任务
        :return:
        """
        if self._current_app_idx < 0 or self._current_app_idx >= len(self._to_run_app_list):
            return self.round_success(status=OneDragonApp.STATUS_ALL_DONE)

        app = self._to_run_app_list[self._current_app_idx]
        app.execute()
        self._current_app_idx += 1

        return self.round_success(status=OneDragonApp.STATUS_NEXT)

    def _after_operation_done(self, result: OperationResult):
        Application._after_operation_done(self, result)
        for app in self.app_list:   # 一条龙结束后 各app恢复
            app.init_context_before_start = True
            app.stop_context_after_stop = True
