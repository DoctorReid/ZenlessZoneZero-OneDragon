from typing import ClassVar

from one_dragon.base.operation.operation import OperationRoundResult, OperationNode
from one_dragon.base.screen.screen_utils import FindAreaResultEnum
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.zzz_operation import ZOperation


class OpenMenu(ZOperation):

    STATUS_NOT_IN_MENU: ClassVar[str] = '未在菜单页面'

    def __init__(self, ctx: ZContext):
        """
        识别画面 打开菜单
        由于使用了返回大世界 应可保证在任何情况下使用
        :param ctx:
        """
        ZOperation.__init__(self, ctx,
                            op_name=gt('打开菜单', 'ui')
                            )

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_menu = OperationNode('画面识别', self.check_menu)
        back_to_world = OperationNode('返回大世界', op=BackToNormalWorld(self.ctx))
        self.add_edge(check_menu, back_to_world, status=OpenMenu.STATUS_NOT_IN_MENU)

        click_menu = OperationNode('点击菜单', self.click_menu)
        self.add_edge(back_to_world, click_menu)
        self.add_edge(click_menu, check_menu)

        self.param_start_node = check_menu

    def check_menu(self) -> OperationRoundResult:
        """
        识别画面
        :return:
        """
        screen = self.screenshot()
        cv2_utils.show_image(screen, win_name='debug')

        result = self.round_by_find_area(screen, '菜单', '更多')
        if result.is_success:
            return self.round_success()
        else:
            return self.round_success(status=OpenMenu.STATUS_NOT_IN_MENU)

    def click_menu(self) -> OperationRoundResult:
        """
        在大世界画面 点击菜单的按钮
        :return:
        """
        click = self.click_area('大世界', '菜单')
        if click:
            return self.round_success(wait=2)
        else:
            return self.round_retry(wait=1)
