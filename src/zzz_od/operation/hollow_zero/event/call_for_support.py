import difflib
from typing import Optional, List, ClassVar

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum
from zzz_od.operation.hollow_zero.event import event_utils
from zzz_od.operation.hollow_zero.event.event_ocr_result_handler import EventOcrResultHandler
from zzz_od.hollow_zero.game_data.hollow_zero_event import HollowZeroSpecialEvent
from zzz_od.operation.zzz_operation import ZOperation


class CallForSupport(ZOperation):

    STATUS_ACCEPT: ClassVar[str] = '接应支援代理人'
    STATUS_NO_NEED: ClassVar[str] = '无需支援'
    OPT_3: ClassVar[str] = '接替小组成员'
    # 每个角色的不接受选项不一样

    def __init__(self, ctx: ZContext):
        """
        确定出现事件后调用
        :param ctx:
        """
        event_name = HollowZeroSpecialEvent.CALL_FOR_SUPPORT.value.event_name
        ZOperation.__init__(
            self, ctx,
            node_max_retry_times=5,
            op_name=gt(event_name)
        )

        self._handlers: List[EventOcrResultHandler] = [
            EventOcrResultHandler(CallForSupport.STATUS_ACCEPT, method=self.check_team, lcs_percent=1),
            EventOcrResultHandler(CallForSupport.OPT_3, self.check_team),
            EventOcrResultHandler(event_name, is_event_mark=True)
        ]

    def handle_init(self):
        self.should_call_pos: int = 0  # 呼叫支援的位置

    @operation_node(name='画面识别', is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        return event_utils.check_event_text_and_run(self, screen, self._handlers)

    def check_team(self, text: str, rect: Rect) -> OperationRoundResult:
        """
        判断当前配队 决定选择的角色
        """
        screen = self.screenshot()
        agent_list = self.ctx.hollow.check_agent_list(screen)

        if agent_list is None:
            return self.round_retry('无法识别当前角色列表', wait=1)

        area = self.ctx.screen_loader.get_area('零号空洞-事件', '呼叫增援-角色行')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)

        agent = self._best_match_agent(ocr_result)
        if agent is None:
            return self.round_retry('无法识别当前增援角色', wait=1)

        self.should_call_pos = self._should_call_backup(agent_list, agent)

        if self.should_call_pos is not None:
            return self.round_success(CallForSupport.STATUS_ACCEPT)
        else:
            return self.round_success(CallForSupport.STATUS_NO_NEED)

    def _best_match_agent(self, ocr_result: str) -> Optional[Agent]:
        idx = ocr_result.find('响应')
        if idx != -1:
            to_match = ocr_result[:idx]
        else:
            to_match = ocr_result

        agent_list: List[Agent] = [agent.value for agent in AgentEnum]
        target_list: List[str] = [gt(agent.value.agent_name) for agent in AgentEnum]

        results = difflib.get_close_matches(to_match, target_list, n=1, cutoff=0.5)

        if results is not None and len(results) > 0:
            idx = target_list.index(results[0])
            return agent_list[idx]
        else:
            return None

    def _should_call_backup(self, agent_list: List[Agent], new_agent: Agent) -> Optional[int]:
        """
        是否应该呼叫增援
        """
        if agent_list[1] is None:
            return 2
        elif agent_list[2] is None:
            return 3
        else:  # TODO 增加优先级
            return None

    @node_from(from_name='画面识别', status=STATUS_ACCEPT)
    @operation_node(name=STATUS_ACCEPT)
    def accept_backup(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)
        return self.round_by_ocr_and_click(screen, CallForSupport.STATUS_ACCEPT, area=area,
                                           success_wait=2, retry_wait=1)

    @node_from(from_name=STATUS_ACCEPT)
    @operation_node(name='选择位置')
    def choose_pos(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)
        cn = '%d号位' % self.should_call_pos
        return self.round_by_ocr_and_click(screen, cn, area=area, lcs_percent=1,
                                           success_wait=2, retry_wait=1)

    @node_from(from_name='选择位置')
    @operation_node(name='确认')
    def confirm(self) -> OperationRoundResult:
        return event_utils.click_empty(self)

    @node_from(from_name='画面识别', status=STATUS_NO_NEED)
    @operation_node(name='拒绝')
    def reject_agent(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = event_utils.get_event_text_area(self)
        opts = [
            '下次再依靠你',  # 本
            '这次没有研究的机会',  # 格蕾丝
            '先不劳烦青衣了',  # 青衣
            '暂不需要援助',  # 丽娜
            '目前不需要支援',  # 派派
            '下次再雇你',  # 妮可
        ]
        for opt in opts:
            result = self.round_by_ocr_and_click(screen, opt, area=area, lcs_percent=0.5)
            if result.is_success:
                 return self.round_success(result.status, wait=2)
        return self.round_retry('未配置对应的代理人选项', wait=1)



def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.start_running()
    ctx.ocr.init_model()
    op = CallForSupport(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()