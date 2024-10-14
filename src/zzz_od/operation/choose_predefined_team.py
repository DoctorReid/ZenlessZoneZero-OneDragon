import time

import difflib
from typing import List

from one_dragon.base.geometry.point import Point
from one_dragon.base.matcher.match_result import MatchResultList
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class ChoosePredefinedTeam(ZOperation):

    def __init__(self, ctx: ZContext, target_team_idx_list: List[int]):
        """
        在出战画面使用
        :param ctx:
        """
        ZOperation.__init__(self, ctx, op_name=gt('选择预备编队', 'ui'))

        self.target_team_idx_list: List[int] = target_team_idx_list

    def handle_init(self):
        pass

    @operation_node(name='画面识别', node_max_retry_times=10, is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '实战模拟室', '预备编队')
        if result.is_success:
            return self.round_success(result.status)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='画面识别', status='预备编队')
    @operation_node(name='点击预备编队')
    def click_team(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '实战模拟室', '预备编队',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击预备编队')
    @operation_node(name='选择编队')
    def choose_team(self) -> OperationRoundResult:
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('实战模拟室', '预备出战')
        result = self.round_by_ocr(screen, '预备出战', area=area,
                                   color_range=[(240, 240, 240), (255, 255, 255)])
        if result.is_success:
            return self.round_success(result.status)

        team_list = self.ctx.team_config.team_list

        for target_team_idx in self.target_team_idx_list:
            if team_list is None or target_team_idx >= len(team_list):
                return self.round_fail('选择的预备编队下标错误 %s' % target_team_idx)

            target_team_name = team_list[target_team_idx].name

            ocr_map = self.ctx.ocr.run_ocr(screen)
            target_list = list(ocr_map.keys())
            best_match = difflib.get_close_matches(target_team_name, target_list, n=1)

            if best_match is None or len(best_match) == 0:
                return self.round_retry(wait=1)

            ocr_result: MatchResultList = ocr_map.get(best_match[0], None)
            if ocr_result is None or ocr_result.max is None:
                return self.round_retry(wait=1)

            to_click = ocr_result.max.center + Point(200, 0)
            self.ctx.controller.click(to_click)

            time.sleep(1)

        return self.round_wait()

    @node_from(from_name='选择编队')
    @operation_node(name='选择编队确认 ')
    def click_confirm(self) -> OperationRoundResult:
        screen = self.screenshot()

        return self.round_by_find_and_click_area(screen, '实战模拟室', '预备出战',
                                                   success_wait=1, retry_wait=1)
