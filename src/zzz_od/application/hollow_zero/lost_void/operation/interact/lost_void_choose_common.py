import time

from cv2.typing import MatLike
from typing import List

from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class LostVoidChooseCommon(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(self, ctx, op_name='迷失之地-通用选择')

        self.to_choose_num: int = 1  # 需要选择的数量

    @operation_node(name='等待加载', node_max_retry_times=10, is_start_node=True)
    def wait_loading(self) -> OperationRoundResult:
        screen_name = self.check_and_update_current_screen()
        if screen_name == '迷失之地-通用选择':
            return self.round_success()
        else:
            return self.round_retry(status=f'当前画面 {screen_name}', wait=1)

    @node_from(from_name='等待加载')
    @operation_node(name='选择')
    def choose_gear(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '迷失之地-通用选择', '标题-武备已升级')
        if result.is_success:
            return result

        art_list = self.get_artifact_pos(screen)
        if len(art_list) == 0:
            return self.round_retry(status='无法识别藏品', wait=1)

        priority_list = self.ctx.lost_void.get_artifact_by_priority(art_list, self.to_choose_num)
        for art in priority_list:
            self.ctx.controller.click(art.center)
            time.sleep(0.5)

        return self.round_success()

    def get_artifact_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取藏品的位置
        @param screen: 游戏画面
        @return: 识别到的武备的位置
        """
        is_gear: bool = False  # 区域-武备名称
        is_artifact: bool = False # 区域-藏品名称

        area = self.ctx.screen_loader.get_area('迷失之地-通用选择', '区域-标题')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr(part)

        target_result_list = [
            gt('请选择1项'),
            gt('请选择2项'),
            gt('请选择1个武备'),
        ]

        for ocr_word in ocr_result.keys():
            idx = str_utils.find_best_match_by_difflib(ocr_word, target_result_list)
            if idx is None:
                continue

            if idx == 0:
                is_artifact = True
                self.to_choose_num = 1
            elif idx == 1:
                is_artifact = True
                self.to_choose_num = 2
            elif idx == 2:
                is_gear = True
                self.to_choose_num = 1

        if is_artifact:
            area_name = '区域-藏品名称'
        elif is_gear:
            area_name = '区域-武备名称'
        else:
            result = self.round_by_find_area(screen, '迷失之地-通用选择', '标题-请选择1个武备')
            if result.is_success:
                area_name = '区域-武备名称'
                self.to_choose_num = 1
            else:
                area_name = '区域-藏品名称'
                self.to_choose_num = 1

        area = self.ctx.screen_loader.get_area('迷失之地-通用选择', area_name)
        part = cv2_utils.crop_image_only(screen, area.rect)

        result_list: List[MatchResult] = []

        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            art = self.ctx.lost_void.match_artifact_by_ocr_full(ocr_result)
            if art is None:
                continue

            result = mrl.max
            result.add_offset(area.left_top)
            result.data = art
            result_list.append(result)

        return result_list

    @node_from(from_name='选择')
    @operation_node(name='点击确定')
    def click_confirm(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-通用选择', area_name='按钮-确定',
                                                 success_wait=1, retry_wait=1,
                                                 until_not_find_all=[('迷失之地-通用选择', '按钮-确定')])


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.lost_void.init_before_run()
    ctx.start_running()

    op = LostVoidChooseCommon(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()