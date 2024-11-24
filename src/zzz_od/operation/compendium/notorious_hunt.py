import time

from typing import Optional, ClassVar

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntLevelEnum
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.choose_predefined_team import ChoosePredefinedTeam
from zzz_od.operation.zzz_operation import ZOperation
from zzz_od.screen_area.screen_normal_world import ScreenNormalWorldEnum


class NotoriousHunt(ZOperation):

    STATUS_NO_LEFT_TIMES: ClassVar[str] = '没有剩余次数'

    def __init__(self, ctx: ZContext, plan: ChargePlanItem):
        """
        使用快捷手册传送后
        用这个进行挑战
        :param ctx:
        """
        ZOperation.__init__(
            self, ctx,
            op_name='%s %s' % (
                gt('恶名狩猎'),
                gt(plan.mission_type_name)
            )
        )

        self.plan: ChargePlanItem = plan
        self.auto_op: Optional[AutoBattleOperator] = None
        self.charge_left: Optional[int] = None
        self.charge_need: Optional[int] = None
        self.move_times: int = 0  # 移动次数

    @operation_node(name='等待入口加载', node_max_retry_times=60, is_start_node=True)
    def wait_entry_load(self) -> OperationRoundResult:
        screen = self.screenshot()
        r1 = self.round_by_find_area(screen, '恶名狩猎', '当期剩余奖励次数')
        if r1.is_success:
            return self.round_success(r1.status)

        r2 = self.round_by_find_area(screen, '恶名狩猎', '剩余奖励次数')
        if r2.is_success:
            self.round_by_click_area('菜单', '返回')
            return self.round_wait(r2.status, wait=1)

        return self.round_retry(r1.status, wait=1)

    @node_from(from_name='等待入口加载')
    @operation_node(name='识别剩余次数')
    def check_left_times(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('恶名狩猎', '剩余次数')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        left_times = str_utils.get_positive_digits(ocr_result, None)

        if left_times is None:
            return self.round_retry('未能识别剩余次数', wait_round_time=1)
        elif left_times == 0:
            self.ctx.notorious_hunt_record.left_times = 0
            return self.round_success(NotoriousHunt.STATUS_NO_LEFT_TIMES)
        else:
            self.ctx.notorious_hunt_record.left_times = left_times
            self.can_run_times = min(left_times, self.plan.plan_times - self.plan.run_times)
            return self.round_success()

    @node_from(from_name='识别剩余次数')
    @operation_node(name='选择副本')
    def choose_mission(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('恶名狩猎', '副本名称列表')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            if str_utils.find_by_lcs(gt(self.plan.mission_type_name), ocr_result, percent=0.5):
                to_click = mrl.max.center + area.left_top + Point(0, 100)
                if self.ctx.controller.click(to_click):
                    return self.round_success(wait=2)

        return self.round_retry(f'未能识别{self.plan.mission_type_name}', wait_round_time=1)

    @node_from(from_name='选择副本')
    @operation_node(name='选择难度')
    def choose_level(self) -> OperationRoundResult:
        if self.plan.level == NotoriousHuntLevelEnum.DEFAULT.value.value:
            return self.round_success()

        self.round_by_click_area('恶名狩猎', '难度选择入口')
        time.sleep(1)

        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('恶名狩猎', '难度选择区域')
        result = self.round_by_ocr_and_click(screen, self.plan.level, area=area,
                                           success_wait=1)
        # 如果选择的是最高难度 那第一下有可能选中不到 多选一下兜底
        self.round_by_ocr_and_click(screen, self.plan.level, area=area,
                                    success_wait=1)
        if result.is_success:
            return result
        else:
            return self.round_retry(result.status, wait=1)

    @node_from(from_name='选择难度')
    @operation_node(name='下一步', node_max_retry_times=10)  # 部分机器加载较慢 延长出战的识别时间
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()

        # 点击直到出战按钮出现
        result = self.round_by_find_area(screen, '实战模拟室', '出战')
        if result.is_success:
            return self.round_success(result.status)

        result = self.round_by_find_and_click_area(screen, '实战模拟室', '下一步')
        if result.is_success:
            time.sleep(0.5)
            self.ctx.controller.mouse_move(ScreenNormalWorldEnum.UID.value.center)  # 点击后 移开鼠标 防止识别不到出战
            return self.round_wait(result.status, wait=0.5)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='下一步')
    @operation_node(name='选择预备编队')
    def choose_predefined_team(self) -> OperationRoundResult:
        if self.plan.predefined_team_idx == -1:
            return self.round_success('无需选择预备编队')
        else:
            op = ChoosePredefinedTeam(self.ctx, [self.plan.predefined_team_idx])
            return self.round_by_op_result(op.execute())

    @node_from(from_name='选择预备编队')
    @operation_node(name='出战')
    def click_start(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(
            screen, '实战模拟室', '出战',
            success_wait=1, retry_wait_round=1
        )

    @node_from(from_name='出战')
    @node_from(from_name='重新开始-确认')
    @operation_node(name='加载自动战斗指令')
    def init_auto_battle(self) -> OperationRoundResult:
        if self.plan.predefined_team_idx == -1:
            auto_battle = self.plan.auto_battle_config
        else:
            team_list = self.ctx.team_config.team_list
            auto_battle = team_list[self.plan.predefined_team_idx].auto_battle

        return auto_battle_utils.load_auto_op(self, 'auto_battle', auto_battle)

    @node_from(from_name='加载自动战斗指令')
    @operation_node(name='等待战斗画面加载', node_max_retry_times=60)
    def wait_battle_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '战斗画面', '按键-普通攻击')
        if result.is_success:
            return self.round_success(self.plan.mission_type_name)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='等待战斗画面加载')
    @operation_node(name='移动靠近交互', node_max_retry_times=10)
    def first_move(self) -> OperationRoundResult:
        if self.plan.mission_type_name == '「霸主侵蚀体·庞培」':
            return self._move_by_hint()
        else:
            if self.node_retry_times == 0:  # 第一次移动较远距离
                self.ctx.controller.move_w(press=True, press_time=0.8, release=True)
            else:
                self.ctx.controller.move_w(press=True, press_time=0.2, release=True)
            time.sleep(1)

            screen = self.screenshot()
            return self.round_by_find_area(screen, '战斗画面', '按键-交互')

    def _move_by_hint(self) -> OperationRoundResult:
        """
        根据画面显示的距离进行移动
        出现交互的按钮时候就可以停止了
        """
        if self.move_times >= 10:
            return self.round_fail()

        screen = self.screenshot()

        result = self.round_by_find_area(screen, '战斗画面', '按键-交互')
        if result.is_success:
            return self.round_success()

        mr = self.auto_op.auto_battle_context.check_battle_distance(screen)
        if mr is None:
            self.distance_pos = None
        else:
            self.distance_pos = mr.rect

        if self.distance_pos is None:
            return self.round_retry(wait=1)

        current_distance = self.auto_op.auto_battle_context.last_check_distance

        pos = self.distance_pos.center
        if pos.x < 900:
            self.ctx.controller.turn_by_distance(-50)
            return self.round_wait(wait=0.5)
        elif pos.x > 1100:
            self.ctx.controller.turn_by_distance(+50)
            return self.round_wait(wait=0.5)
        else:
            self.last_distance = current_distance
            press_time = self.auto_op.auto_battle_context.last_check_distance / 7.2  # 朱鸢测出来的速度
            self.ctx.controller.move_w(press=True, press_time=press_time, release=True)
            self.move_times += 1
            return self.round_wait(wait=0.5)

    @node_from(from_name='移动靠近交互')
    @operation_node(name='交互')
    def move_and_interact(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '战斗画面', '按键-交互')
        if result.is_success:
            self.ctx.controller.interact(press=True, press_time=0.2, release=True)
            time.sleep(2)
            return self.round_retry()
        else:
            return self.round_success()

    @node_from(from_name='交互')
    @operation_node(name='选择')
    def choose_buff(self) -> OperationRoundResult:
        screen = self.screenshot()

        # TODO 当前没有选择鸣徽的优先级

        return self.round_by_find_and_click_area(screen, '恶名狩猎', '选择',
                                                 success_wait=1, retry_wait_round=1)

    @node_from(from_name='选择')
    @operation_node(name='向前移动准备战斗')
    def move_to_battle(self) -> OperationRoundResult:
        self.ctx.controller.move_w(press=True, press_time=3, release=True)
        self.auto_op.start_running_async()
        return self.round_success()

    @node_from(from_name='向前移动准备战斗')
    @node_from(from_name='战斗失败', status='战斗结果-倒带')
    @operation_node(name='自动战斗', mute=True)
    def auto_battle(self) -> OperationRoundResult:
        if self.auto_op.auto_battle_context.last_check_end_result is not None:
            auto_battle_utils.stop_running(self.auto_op)
            return self.round_success(status=self.auto_op.auto_battle_context.last_check_end_result)
        now = time.time()
        screen = self.screenshot()

        self.auto_op.auto_battle_context.check_battle_state(screen, now, check_battle_end_normal_result=True)

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗', status='普通战斗-撤退')
    @operation_node(name='战斗失败')
    def battle_fail(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-倒带')

        if result.is_success:
            self.auto_op.auto_battle_context.last_check_end_result = None
            self.auto_op.start_running_async()
            return self.round_success(result.status, wait=1)

        result = self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-撤退')
        if result.is_success:
            return self.round_success(result.status, wait=1)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='战斗失败', status='战斗结果-撤退')
    @operation_node(name='战斗失败退出')
    def battle_fail_exit(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-退出')

        if result.is_success:  # 战斗失败 返回失败到外层 中断后续挑战
            return self.round_fail(result.status, wait=10)
        else:
            return self.round_retry(result.status, wait=1)

    @node_from(from_name='自动战斗')
    @operation_node(name='战斗结束')
    def after_battle(self) -> OperationRoundResult:
        self.can_run_times -= 1
        self.ctx.notorious_hunt_record.left_times = self.ctx.notorious_hunt_record.left_times - 1
        self.ctx.notorious_hunt_config.add_plan_run_times(self.plan)
        return self.round_success()

    @node_from(from_name='战斗结束')
    @operation_node(name='判断下一次')
    def check_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        if self.can_run_times == 0:
            return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-完成',
                                                     success_wait=5, retry_wait_round=1)
        else:
            return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-再来一次',
                                                     success_wait=1, retry_wait_round=1)

    @node_from(from_name='判断下一次', success=False)
    @operation_node(name='判断下一次失败处理')
    def no_left_times(self) -> OperationRoundResult:
        # 本地记录的剩余次数错误 找不到再来一次
        # 可能在其它设备上完成了挑战 也可能是上面识别错了
        self.ctx.notorious_hunt_record.left_times = 0
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-完成',
                                                 success_wait=5, retry_wait_round=1)

    @node_from(from_name='判断下一次', status='战斗结果-再来一次')
    @operation_node(name='重新开始-确认')
    def restart_confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '恶名狩猎', '重新开始-确认',
                                                 success_wait=1, retry_wait_round=1)

    @node_from(from_name='判断下一次', status='战斗结果-完成')
    @node_from(from_name='判断下一次失败处理', status='战斗结果-完成')
    @operation_node(name='等待返回入口', node_max_retry_times=60)
    def wait_back_to_entry(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_area(
            screen, '恶名狩猎', '剩余奖励次数',
            success_wait=1, retry_wait=1
        )

    @node_from(from_name='移动靠近交互', success=False)
    @operation_node(name='交互失败')
    def fail_to_interact(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '恶名狩猎', '退出战斗')
        if result.is_success:
            return self.round_success(wait=1)  # 稍微等一下让按钮可按

        result = self.round_by_click_area('战斗画面', '菜单')
        if result.is_success:
            return self.round_wait(result.status, wait=2)
        else:
            return self.round_fail(result.status)

    @node_from(from_name='交互失败')
    @operation_node(name='点击退出战斗')
    def click_exit_battle(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '恶名狩猎', '退出战斗',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击退出战斗')
    @operation_node(name='点击退出战斗确认')
    def click_exit_battle_confirm(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '恶名狩猎', '退出战斗-确认',
                                                 success_wait=5, retry_wait=1)

    @node_from(from_name='点击退出战斗确认')
    @operation_node(name='点击退出')
    def click_exit(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_and_click_area(screen, '战斗画面', '战斗结果-退出')

        if result.is_success:  # 战斗失败 返回失败到外层 中断后续挑战
            return self.round_fail(result.status, wait=10)
        else:
            return self.round_retry(result.status, wait=1)

    def _on_pause(self, e=None):
        ZOperation._on_pause(self, e)
        if self.auto_op is not None:
            self.auto_op.stop_running()

    def _on_resume(self, e=None):
        ZOperation._on_resume(self, e)
        auto_battle_utils.resume_running(self.auto_op)

    def after_operation_done(self, result: OperationResult):
        ZOperation.after_operation_done(self, result)
        if self.auto_op is not None:
            self.auto_op.dispose()
            self.auto_op = None


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    op = NotoriousHunt(ctx, ChargePlanItem(
        category_name='恶名狩猎',
        mission_type_name='冥宁芙·双子',
        level=NotoriousHuntLevelEnum.DEFAULT.value.value,
        auto_battle_config='专属配队-简',
        predefined_team_idx=0
    ))
    op.can_run_times = 1
    op.auto_op = None
    op.init_auto_battle()

    op.execute()


if __name__ == '__main__':
    __debug()
