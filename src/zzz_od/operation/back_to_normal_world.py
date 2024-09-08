from cv2.typing import MatLike

from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import AgentEnum
from zzz_od.hollow_zero.event import hollow_event_utils
from zzz_od.hollow_zero.hollow_exit_by_menu import HollowExitByMenu
from zzz_od.operation.zzz_operation import ZOperation


class BackToNormalWorld(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        需要保证在任何情况下调用，都能返回大世界，让后续的应用可执行
        :param ctx:
        """
        ZOperation.__init__(self, ctx, op_name=gt('返回大世界', 'ui'))

    def handle_init(self):
        pass

    @operation_node(name='画面识别', is_start_node=True, node_max_retry_times=60)
    def check_screen_and_run(self) -> OperationRoundResult:
        """
        识别游戏画面
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '大世界', '信息')

        if result.is_success:
            return self.round_success()

        # 这是领取完活跃度奖励的情况
        result = self.round_by_find_area(screen, '快捷手册', 'TAB-挑战')
        if result.is_success:
            self.click_area('快捷手册', '退出')
            return self.round_retry(wait=1)

        # 判断是否有好感度事件
        if self._check_agent_dialog(screen):
            return self._handle_agent_dialog(screen)

        # 判断在战斗画面
        result = self.round_by_find_area(screen, '战斗画面', '按键-普通攻击')
        if result.is_success:
            self.click_area('战斗画面', '菜单')
            return self.round_retry(wait=1)
        # 空洞内的撤退
        result = self.round_by_find_and_click_area(screen, '零号空洞-战斗', '退出战斗')
        if result.is_success:
            return self.round_retry(wait=1)
        # 空洞内撤退后的完成
        result = self.round_by_find_and_click_area(screen, '零号空洞-事件', '通关-完成')
        if result.is_success:
            return self.round_retry(wait=1)
        # 在空洞内
        result = hollow_event_utils.check_in_hollow(self.ctx, screen)
        if result is not None:
            op = HollowExitByMenu(self.ctx)
            op.execute()
            return self.round_retry(wait=1)

        click_back = self.click_area('菜单', '返回')
        if click_back:
            return self.round_retry(wait_round_time=1)
        else:
            return self.round_fail()

    def _check_agent_dialog(self, screen: MatLike) -> bool:
        """
        识别是否有代理人好感度对话
        """
        area = self.ctx.screen_loader.get_area('大世界', '好感度标题')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        ocr_result_list = [i for i in ocr_result_map.keys()]
        agent_name_list = [gt(i.value.agent_name) for i in AgentEnum]
        idx1, idx2 = str_utils.find_most_similar(ocr_result_list, agent_name_list)
        return idx1 is not None and idx2 is not None

    def _handle_agent_dialog(self, screen: MatLike) -> OperationRoundResult:
        """
        处理代理人好感度对话
        """
        area = self.ctx.screen_loader.get_area('大世界', '好感度选项')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        if len(ocr_result_map) > 0:
            for ocr_result, mrl in ocr_result_map.items():
                self.ctx.controller.click(mrl.max.center + area.left_top)
                return self.round_wait(ocr_result, wait=1)
        else:
            self.click_area('菜单', '返回')
            return self.round_wait('对话无选项', wait=1)


def __debug_op():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    op = BackToNormalWorld(ctx)
    ctx.start_running()
    op.execute()


if __name__ == '__main__':
    __debug_op()