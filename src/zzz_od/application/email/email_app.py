from one_dragon.base.operation.operation import OperationNode, OperationRoundResult
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.open_menu import OpenMenu


class EmailApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='email',
            op_name=gt('邮件', 'ui'),
            run_record=ctx.email_run_record
        )

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        open_menu = OperationNode('打开菜单', op=OpenMenu(self.ctx))
        click_email = OperationNode('点击邮件', self.click_email)  # TODO 是否需要红点检测
        self.add_edge(open_menu, click_email)

        click_get_all = OperationNode('全部领取', self.click_get_all)
        self.add_edge(click_email, click_get_all)

        click_confirm = OperationNode('确认', self.click_confirm)
        self.add_edge(click_get_all, click_confirm)

        back_to_menu = OperationNode('返回菜单', self.back_to_menu)
        self.add_edge(click_confirm, back_to_menu)
        self.add_edge(click_confirm, back_to_menu, success=False)  # 没有东西领取的话 就不会有确认按钮

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def click_email(self) -> OperationRoundResult:
        """
        在菜单页面 点击邮件
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '菜单', '邮件',
                                                 success_wait=1, retry_wait_round=1)

    def click_get_all(self) -> OperationRoundResult:
        """
        邮件画面 点击全部领取
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '邮件', '全部领取',
                                                 success_wait=1, retry_wait_round=1)

    def click_confirm(self) -> OperationRoundResult:
        """
        邮件画面 领取后点击确认
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '邮件', '确认',
                                                 success_wait=1, retry_wait_round=1)

    def back_to_menu(self) -> OperationRoundResult:
        """
        返回菜单
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '邮件', '返回',
                                                 success_wait=1, retry_wait_round=1)
