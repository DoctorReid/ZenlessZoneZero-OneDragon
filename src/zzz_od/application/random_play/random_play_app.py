import time

import difflib
from typing import List, ClassVar

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.transport import Transport
from zzz_od.operation.wait_normal_world import WaitNormalWorld


class RandomPlayApp(ZApplication):

    STATUS_ALL_VIDEO_CHOOSE: ClassVar[str] = '已选择全部录像带'
    STATUS_ALREADY_RUNNING: ClassVar[str] = '正在营业'

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='random_play',
            node_max_retry_times=10,
            op_name=gt('影像店营业', 'ui'),
            run_record=ctx.random_play_run_record
        )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self._all_video_themes: List[str] = [
            '纪实', '怀旧', '冒险', '幻想', '喜剧', '动作', '惊悚', '悬疑',
            '访谈', '都市', '时尚', '灾难', '悲剧', '亲情', '广告', '爱情',
        ]
        self._need_video_themes: List[str] = []
        self._current_idx: int = 0

    @operation_node(name='传送', is_start_node=True)
    def transport(self) -> OperationRoundResult:
        op = Transport(self.ctx, 'Random Play', '柜台')
        return self.round_by_op(op.execute())

    @node_from(from_name='传送')
    @operation_node(name='等待加载')
    def wait_world(self) -> OperationRoundResult:
        op = WaitNormalWorld(self.ctx)
        return self.round_by_op(op.execute())

    @node_from(from_name='等待加载')
    @operation_node(name='移动交互')
    def move_and_interact(self) -> OperationRoundResult:
        """
        传送之后 往前移动一下 方便交互
        :return:
        """
        self.ctx.controller.move_w(press=True, press_time=1, release=True)
        time.sleep(1)

        self.ctx.controller.interact(press=True, press_time=0.2, release=True)
        time.sleep(5)

        return self.round_success()

    @node_from(from_name='移动交互')
    @operation_node(name='等待经营画面加载')
    def wait_run(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '影像店营业', '昨日账本')
        if result.is_success:
            return self.round_by_click_area('影像店营业', '返回',
                                            success_wait=1, retry_wait=1)
        # 看看经营状况
        return self.round_by_find_area(screen, '影像店营业', '经营状况',
                                       success_wait=1, retry_wait=1)

    @node_from(from_name='等待经营画面加载')
    @operation_node(name='识别营业状态')
    def check_running(self) -> OperationRoundResult:
        screen = self.screenshot()

        # 防止上一步跳过了昨日账本
        result = self.round_by_find_area(screen, '影像店营业', '昨日账本')
        if result.is_success:
            self.round_by_click_area('影像店营业', '返回')
            return self.round_retry(wait=1)

        result = self.round_by_find_area(screen, '影像店营业', '正在营业')
        if result.is_success:
            return self.round_success(RandomPlayApp.STATUS_ALREADY_RUNNING)
        else:
            return self.round_success()

    @node_from(from_name='识别营业状态')
    @operation_node(name='点击宣传员入口')
    def click_promoter_entry(self) -> OperationRoundResult:
        """
        在经营状况页面 点击代理人的位置
        :return:
        """
        return self.round_by_click_area('影像店营业', '宣传员入口',
                                        success_wait=1, retry_wait=1)

    @node_from(from_name='点击宣传员入口')
    @operation_node(name='选择宣传员')
    def choose_promoter(self) -> OperationRoundResult:
        """
        在经营状况页面 点击代理人的位置
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '影像店营业', '选择宣传员')
        if not result.is_success:
            return self.round_retry(status=result.status, wait_round_time=1)

        dt = self.run_record.get_current_dt()
        idx = (int(dt[-1]) % 2) + 1

        self.click_area('影像店营业', '宣传员-%d' % idx)
        time.sleep(0.5)

        return self.round_by_find_and_click_area(screen, '影像店营业', '确认')

    @node_from(from_name='选择宣传员')
    @operation_node(name='识别录像带主题')
    def check_video_theme(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '影像店营业', '经营状况')
        if not result.is_success:
            return self.round_retry(status=result.status, wait=1)

        areas = [
            self.ctx.screen_loader.get_area('影像店营业', '录像带主题-1'),
            self.ctx.screen_loader.get_area('影像店营业', '录像带主题-2'),
            self.ctx.screen_loader.get_area('影像店营业', '录像带主题-3')
        ]

        target_list = [gt(i) for i in self._all_video_themes]
        for area in areas:
            part = cv2_utils.crop_image_only(screen, area.rect)
            ocr_result = self.ctx.ocr.run_ocr_single_line(part)

            results = difflib.get_close_matches(ocr_result, target_list, n=1)

            if results is not None and len(results) > 0:
                idx = target_list.index(results[0])
                self._need_video_themes.append(self._all_video_themes[idx])

        return self.round_success()

    @node_from(from_name='识别录像带主题')
    @operation_node(name='点击录像带入口')
    def click_video_entry(self) -> OperationRoundResult:
        """
        在经营状况页面 点击录像带的位置
        :return:
        """
        return self.round_by_click_area('影像店营业', '录像带入口',
                                        success_wait=1, retry_wait=1)

    @node_from(from_name='点击录像带入口')
    @operation_node(name='识别推荐上架')
    def check_recommended(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = self.round_by_find_and_click_area(screen, '影像店营业', '推荐上架')

        if result.is_success:
            return self.round_success(status=result.status, wait=1)

        return self.round_by_find_area(screen, '影像店营业', '上架筛选')

    @node_from(from_name='识别推荐上架', status='上架筛选')
    @node_from(from_name='上架')
    @operation_node(name='上架筛选')
    def click_filter(self) -> OperationRoundResult:
        """
        在录像带画面 点击上架筛选
        :return:
        """
        if self._current_idx >= len(self._need_video_themes):
            return self.round_success(status=RandomPlayApp.STATUS_ALL_VIDEO_CHOOSE)

        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '影像店营业', '上架筛选',
                                                 success_wait=0.5, retry_wait=1)

    @node_from(from_name='上架筛选')
    @operation_node(name='选择主题')
    def choose_theme(self) -> OperationRoundResult:
        """
        选择主题
        :return:
        """
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('影像店营业', '主题筛选')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_results = self.ctx.ocr.run_ocr(part)

        target_list = [gt(i) for i in self._all_video_themes]
        current_target = self._need_video_themes[self._current_idx]
        for ocr_str, mrl in ocr_results.items():
            if mrl.max is None:
                continue

            results = difflib.get_close_matches(ocr_str, target_list, n=1)

            if results is None or len(results) == 0:
                continue

            idx = target_list.index(results[0])
            theme = self._all_video_themes[idx]
            if theme != current_target:
                continue

            target_point = area.left_top + mrl.max
            if self.ctx.controller.click(target_point):
                return self.round_success(wait=1)
            else:
                return self.round_retry(wait=0.5)

        # 找不到 往下滑动
        start = area.center
        end = start + Point(0, -100)
        self.ctx.controller.drag_to(start=start, end=end)
        return self.round_retry(status='未找到%s' % current_target, wait=1)

    @node_from(from_name='选择主题')
    @operation_node(name='上架')
    def choose_onshelf(self) -> OperationRoundResult:
        """
        上架
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '影像店营业', '下架')
        if result.is_success:  # 已经上架了
            self._current_idx += 1
            return self.round_success()

        result = self.round_by_find_area(screen, '影像店营业', '上架')
        if not result.is_success:
            return self.round_retry(status=result.status, wait_round_time=1)

        click1 = self.round_by_click_area('影像店营业', '上架')
        time.sleep(0.5)
        click2 = self.round_by_click_area('影像店营业', '上架')
        time.sleep(0.5)

        if click1.is_success and click2.is_success:
            return self.round_wait(wait=1)
        else:
            return self.round_retry(status=click1.status, wait_round_time=1)

    @node_from(from_name='识别推荐上架', status='推荐上架')
    @node_from(from_name='上架筛选', status=STATUS_ALL_VIDEO_CHOOSE)
    @operation_node(name='返回')
    def back(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '影像店营业', '经营状况')
        if result.is_success:
            return self.round_success()

        return self.round_by_click_area('影像店营业', '返回', success_wait=1, retry_wait=1)

    @node_from(from_name='返回')
    @operation_node(name='开始营业')
    def start(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '影像店营业', '开始营业',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='开始营业')
    @operation_node(name='开始营业确认')
    def confirm(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '影像店营业', '开始营业-确认',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='开始营业确认')
    @node_from(from_name='识别营业状态', status=STATUS_ALREADY_RUNNING)
    @operation_node(name='返回大世界')
    def back_to_world(self) -> OperationRoundResult:
        op = BackToNormalWorld(self.ctx)
        return self.round_by_op(op.execute())


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = RandomPlayApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()