import time

from cv2.typing import MatLike
from typing import List

from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, cal_utils
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class LostVoidChooseGear(ZOperation):

    def __init__(self, ctx: ZContext):
        ZOperation.__init__(self, ctx, op_name='迷失之地-武备选择')

    @operation_node(name='等待加载', node_max_retry_times=10, is_start_node=True)
    def wait_loading(self) -> OperationRoundResult:
        screen_name = self.check_and_update_current_screen()
        if screen_name == '迷失之地-武备选择':
            return self.round_success()
        else:
            return self.round_retry(wait=1)

    @node_from(from_name='等待加载')
    @operation_node(name='选择武备')
    def choose_gear(self) -> OperationRoundResult:
        screen_list = []
        for i in range(10):
            screen_list.append(self.screenshot())
            time.sleep(0.1)

        gear_list = self.get_gear_pos(screen_list)
        if len(gear_list) == 0:
            # 识别耗时比较长 这里返回就不等待了
            return self.round_retry(status='无法识别武备')

        priority_list = self.ctx.lost_void.get_artifact_by_priority(gear_list, 1)
        for art in priority_list:
            self.ctx.controller.click(art.center)
            time.sleep(0.5)

        return self.round_success(wait=0.5)

    def get_gear_pos(self, screen_list: List[MatLike]) -> List[MatchResult]:
        """
        获取武备的位置
        @param screen_list: 游戏截图列表 由于武备的图像是动态的 需要多张识别后合并结果
        @return: 识别到的武备的位置
        """
        area = self.ctx.screen_loader.get_area('迷失之地-武备选择', '武备列表')
        to_check_list = [
            i
            for i in self.ctx.lost_void.all_artifact_list
            if i.template_id is not None
        ]
        # TODO 后续只识别优先级中的武备

        result_list: List[MatchResult] = []

        for screen in screen_list:
            part = cv2_utils.crop_image_only(screen, area.rect)
            source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
            for gear in to_check_list:
                template = self.ctx.template_loader.get_template('lost_void', gear.template_id)
                if template is None:
                    continue

                template_kps, template_desc = template.features
                mr = cv2_utils.feature_match_for_one(
                    source_kps, source_desc,
                    template_kps, template_desc,
                    template_width=template.raw.shape[1], template_height=template.raw.shape[0],
                    knn_distance_percent=0.7
                )

                if mr is None:
                    continue

                mr.add_offset(area.left_top)
                mr.data = gear

                existed = False
                for existed_result in result_list:
                    if cal_utils.distance_between(existed_result.center, mr.center) < existed_result.rect.width // 2:
                        existed = True
                        break

                if not existed:
                    result_list.append(mr)

        return result_list

    @node_from(from_name='选择武备')
    @operation_node(name='点击携带')
    def click_equip(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-武备选择', area_name='按钮-携带',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='选择武备', success=False)
    @node_from(from_name='点击携带')
    @operation_node(name='点击返回')
    def click_back(self) -> OperationRoundResult:
        return self.round_by_find_and_click_area(screen_name='迷失之地-武备选择', area_name='按钮-返回',
                                                 success_wait=1, retry_wait=1)


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.lost_void.init_before_run()
    ctx.start_running()

    op = LostVoidChooseGear(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()