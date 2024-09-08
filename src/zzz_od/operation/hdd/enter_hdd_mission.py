from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class EnterHddMission(ZOperation):

    def __init__(self, ctx: ZContext,
                 chapter: str,
                 mission_type: str,
                 mission_name: str):
        """
        需要刚进来HDD画面时使用
        :param ctx:
        """
        ZOperation.__init__(self, ctx, op_name=gt('进入HDD副本', 'ui'))

        self.chapter: str = chapter
        self.mission_type: str = mission_type
        self.mission_name: str = mission_name

    def handle_init(self):
        pass

    @operation_node(name='选择章节', is_start_node=True)
    def choose_chapter(self) -> OperationRoundResult:
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('HDD', '章节列表')
        result = self.round_by_ocr_and_click(screen, self.chapter, area=area)
        if result.is_success:
            return self.round_wait(status=result.status, wait=1)

        area = self.ctx.screen_loader.get_area('HDD', '章节显示')
        result = self.round_by_ocr(screen, self.chapter, area=area)
        if result.is_success:
            return self.round_success(status=result.status)

        # 不符合时 点击弹出选项
        result = self.round_by_click_area('HDD', '章节显示')
        return self.round_retry(status=result.status, wait=1)

    @node_from(from_name='选择章节')
    @operation_node(name='选择委托')
    def choose_mission_type(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('HDD', '委托区域')
        result = self.round_by_ocr_and_click(screen, self.mission_type, area=area)
        if result.is_success:
            return self.round_wait(status=result.status, wait=2)

        # 点击知道看到下一步
        result = self.round_by_find_area(screen, 'HDD', '下一步')
        if result.is_success:
            return self.round_success()

    @node_from(from_name='选择委托')
    @operation_node(name='选择副本')
    def choose_mission(self) -> OperationRoundResult:
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('HDD', '副本区域')
        result = self.round_by_ocr_and_click(screen, self.mission_name, area=area)
        if result.is_success:
            return self.round_success(wait=1)

        # 找不到时候 往下滑
        drag_from = area.center
        drag_to = drag_from + Point(0, -100)
        self.ctx.controller.drag_to(start=drag_from, end=drag_to)

        return self.round_retry(wait=1)

    @node_from(from_name='选择副本')
    @operation_node(name='下一步')
    def click_next(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, 'HDD', '下一步',
                                                 success_wait=2, retry_wait=1)

    @node_from(from_name='下一步')
    @operation_node(name='出战')
    def click_deploy(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, 'HDD', '出战',
                                                 success_wait=2, retry_wait=1)
