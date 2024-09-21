import time

from cv2.typing import MatLike
from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.context_event_bus import ContextEventItem
from one_dragon.base.operation.one_dragon_context import ContextKeyboardEventEnum
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.commission_assistant.commission_assistant_config import DialogOptionEnum
from zzz_od.application.zzz_application import ZApplication
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.hollow_zero.event import hollow_event_utils


class CommissionAssistantApp(ZApplication):

    def __init__(self, ctx: ZContext):
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='commission_assistant',
            op_name=gt('委托助手', 'ui'),
        )

        self.run_mode: int = 0  # 0=对话 1=闪避 2=自动战斗
        self.auto_op: Optional[AutoBattleOperator] = None  # 战斗指令

    def handle_init(self):
        self._listen_btn()

    def _unlisten_btn(self) -> None:
        self.ctx.unlisten_all_event(self)

    def _listen_btn(self) -> None:
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def _on_key_press(self, event: ContextEventItem):
        if not self.ctx.is_context_running:
            return
        key = event.data
        if key == self.ctx.commission_assistant_config.dodge_switch:
            if self.run_mode == 0:
                self.run_mode = 1
            elif self.run_mode == 1:
                self.run_mode = 0
        elif key == self.ctx.commission_assistant_config.auto_battle_switch:
            if self.run_mode == 0:
                self.run_mode = 2
            elif self.run_mode == 2:
                self.run_mode = 0

    @node_from(from_name='自动战斗模式')
    @operation_node(name='自动对话模式', is_start_node=True)
    def dialog_mode(self) -> OperationRoundResult:
        if self.run_mode in [1, 2]:
            return self.round_success()

        config = self.ctx.commission_assistant_config
        now = time.time()
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '大世界', '信息')
        if result.is_success:
            return self.round_wait(status='大世界', wait=1)

        result = self.round_by_find_area(screen, '委托助手', '左上角返回')
        # 很多二级菜单都有这个按钮
        if result.is_success:
            return self.round_wait(result.status, wait=1)

        result = self.round_by_find_area(screen, '委托助手', '对话框确认')
        # 一些对话时出现确认
        if result.is_success:
            return self.round_wait(result.status, wait=1)

        # 判断是否在空洞中
        result = hollow_event_utils.check_in_hollow(self.ctx, screen)
        if result is not None:
            return self._handle_hollow(screen, now)

        # 判断是否空洞内完成
        result = self.round_by_find_and_click_area(screen, '零号空洞-事件', '通关-完成')
        if result.is_success:
            return self.round_wait(result.status, wait=1)

        result = self.round_by_find_area(screen, '委托助手', '右上角自动')
        in_auto = result.is_success
        if in_auto and not config.dialog_click_when_auto:
            return self.round_wait(status='自动剧情播放中', wait=1)
        else:
            if self._click_dialog_options(screen, '右侧选项区域'):
                return self.round_wait(status='点击右方选项',
                                       wait=config.dialog_click_interval)

            if self._click_dialog_options(screen, '中间选项区域'):
                return self.round_wait(status='点击中间选项',
                                       wait=config.dialog_click_interval)

            with_dialog = self._check_dialog(screen)
            if with_dialog:
                self.round_by_click_area('委托助手', '中间选项区域')
                return self.round_wait(status='对话中点击空白',
                                       wait=config.dialog_click_interval)

        self.round_by_click_area('委托助手', '中间选项区域')
        return self.round_wait(status='未知画面点击空白', wait=1)

    def _check_dialog(self, screen: MatLike) -> bool:
        """
        识别当前是否有对话
        """
        area = self.ctx.screen_loader.get_area('委托助手', '对话框标题')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result in ocr_result_map.keys():
            if str_utils.with_chinese(ocr_result):
                return True
        return False

    def _click_dialog_options(self, screen: MatLike, area_name: str) -> bool:
        """
        点击对话选项
        """
        area = self.ctx.screen_loader.get_area('委托助手', area_name)
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        if len(ocr_result_map) == 0:
            return False

        to_click: Optional[Point] = None
        for ocr_result, mrl in ocr_result_map.items():
            opt_point = mrl.max.center + area.left_top
            if self.ctx.commission_assistant_config.dialog_option == DialogOptionEnum.LAST.value.value:
                if to_click is None or opt_point.y > to_click.y:  # 最后一个选项 找y轴最大的
                    to_click = opt_point
            else:
                if to_click is None or opt_point.y < to_click.y:  # 第一个选项 找y轴最小的
                    to_click = opt_point
        self.ctx.controller.click(to_click)
        return True

    def _handle_hollow(self, screen: MatLike, screenshot_time: float) -> OperationRoundResult:
        """
        处理在空洞里的情况
        :param screen: 游戏画面
        :param screenshot_time: 截图时间
        """
        # 空洞内不好处理事件
        return self.round_wait(status='空洞中', wait=1)
        self.ctx.hollow.init_event_yolo(True)

        # 判断当前邦布是否存在
        hollow_map = self.ctx.hollow.check_current_map(screen, screenshot_time)
        if hollow_map is None or hollow_map.contains_entry('当前'):
            return self.round_wait(status='空洞走格子中', wait=1)

        # 处理对话
        return hollow_event_utils.check_event_text_and_run(self, screen, [])

    @node_from(from_name='自动对话模式')
    @operation_node(name='自动战斗模式')
    def auto_mode(self) -> OperationRoundResult:
        if self.run_mode == 0:
            return self.round_success()
        self._load_auto_op()

        now = time.time()

        screen = self.screenshot()
        self.auto_op.auto_battle_context.check_battle_state(screen, now)

        return self.round_wait(wait_round_time=self.ctx.battle_assistant_config.screenshot_interval)

    def _load_auto_op(self) -> None:
        """
        加载战斗指令
        """
        if self.auto_op is None:
            auto_battle_utils.load_auto_op(self,
                                           'auto_battle' if self.run_mode == 2 else 'dodge',
                                           self.ctx.commission_assistant_config.auto_battle if self.run_mode == 2 else self.ctx.commission_assistant_config.dodge_config)
        self.auto_op.start_running_async()

    def handle_pause(self):
        ZApplication.handle_pause(self)
        self._unlisten_btn()
        auto_battle_utils.stop_running(self.auto_op)

    def handle_resume(self) -> None:
        ZApplication.handle_resume(self)
        self._listen_btn()
        auto_battle_utils.resume_running(self.auto_op)

    def after_operation_done(self, result: OperationResult):
        ZApplication.after_operation_done(self, result)
        self._unlisten_btn()
        if self.auto_op is not None:
            self.auto_op.dispose()
            self.auto_op = None

def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = CommissionAssistantApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()