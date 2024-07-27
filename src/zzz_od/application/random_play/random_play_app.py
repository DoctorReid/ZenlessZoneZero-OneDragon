from one_dragon.base.operation.operation import OperationNode
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.transport import Transport


class RandomPlayApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        每天自动接收邮件奖励
        """
        ZApplication.__init__(
            self,
            ctx=ctx, app_id='random_play',
            op_name=gt('影像店营业', 'ui'),
            run_record=ctx.email_run_record
        )

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        tp = OperationNode('传送', op=Transport(self.ctx, 'Random Play', '柜台'))
        move = OperationNode('往前移动', )

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        pass

    def move_and_interact(self) -> None:
        """
        传送之后 往前移动一下 方便交互
        :return:
        """
        screen = self.screenshot()