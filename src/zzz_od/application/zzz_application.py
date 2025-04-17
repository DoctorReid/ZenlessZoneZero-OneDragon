from typing import Optional, Callable

from one_dragon.base.notify.push import Push
from one_dragon.base.operation.application_base import Application
from one_dragon.base.operation.application_run_record import AppRunRecord
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_round_result import OperationRoundResult

from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.enter_game.open_and_enter_game import OpenAndEnterGame


class ZApplication(Application):

    def __init__(self, ctx: ZContext, app_id: str,
                 node_max_retry_times: int = 1,
                 op_name: str = None,
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 need_check_game_win: bool = True,
                 init_context_before_start: bool = True,
                 stop_context_after_stop: bool = True,
                 run_record: Optional[AppRunRecord] = None,
                 need_ocr: bool = True,
                 retry_in_od: bool = False
                 ):
        self.ctx: ZContext = ctx
        op_to_enter_game = OpenAndEnterGame(ctx)
        Application.__init__(self,
                             ctx=ctx, app_id=app_id,
                             node_max_retry_times=node_max_retry_times,
                             op_name=op_name,
                             timeout_seconds=timeout_seconds,
                             op_callback=op_callback,
                             need_check_game_win=need_check_game_win,
                             op_to_enter_game=op_to_enter_game,
                             init_context_before_start=init_context_before_start,
                             stop_context_after_stop=stop_context_after_stop,
                             run_record=run_record,
                             need_ocr=need_ocr,
                             retry_in_od=retry_in_od
                             )

    def handle_resume(self) -> None:
        self.ctx.controller.active_window()
        Application.handle_resume(self)

    def notify(self) -> None:
        """
        发送通知，在应用内部调用
        :return:
        """
        if not self.ctx.notify_config.enable_notify:
            return

        app_id = getattr(self, 'app_id', None)
        app_name = getattr(self, 'op_name', None)

        if not getattr(self.ctx.notify_config, app_id, False):
            return

        message = f"任务「{app_name}」运行成功\n"
        image = None
        if self.ctx.push_config.send_image:
            image = self.save_screenshot_bytes()

        pusher = Push(self.ctx)
        pusher.send(message, image)
