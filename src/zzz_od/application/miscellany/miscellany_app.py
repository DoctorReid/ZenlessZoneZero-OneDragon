from typing import List

from one_dragon.base.operation.one_dragon_app import OneDragonApp
from zzz_od.application.email_app.email_app import EmailApp
from zzz_od.application.life_on_line.life_on_line_app import LifeOnLineApp
from zzz_od.application.redemption_code.redemption_code_app import RedemptionCodeApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.enter_game.open_and_enter_game import OpenAndEnterGame


class MiscellanyApp(OneDragonApp, ZApplication):

    def __init__(self, ctx: ZContext):
        app_id = 'miscellany'
        op_to_enter_game = OpenAndEnterGame(ctx)
        op_to_switch_account = None

        ZApplication.__init__(self, ctx, app_id, run_record=ctx.miscellany_record)
        OneDragonApp.__init__(self, ctx, app_id,
                              op_name='杂项',
                              op_to_enter_game=op_to_enter_game,
                              op_to_switch_account=op_to_switch_account)

    def handle_init(self) -> None:
        """
        只运行当前实例
        """
        current_instance = self.ctx.one_dragon_config.current_active_instance
        self._instance_list = [current_instance]
        self._instance_start_idx = 0
        self._instance_idx = self._instance_start_idx

    def get_app_list(self) -> List[ZApplication]:
        return [
            RedemptionCodeApp(self.ctx),
            EmailApp(self.ctx),
            LifeOnLineApp(self.ctx),
        ]

    def get_app_order_list(self) -> List[str]:
        """
        获取应用运行顺序
        :return: app id list
        """
        return self.ctx.miscellany_config.app_order

    def update_app_order_list(self, new_app_orders: List[str]) -> None:
        """
        更新引用运行顺序
        :param new_app_orders: app id list
        :return:
        """
        self.ctx.miscellany_config.app_order = new_app_orders


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    app = MiscellanyApp(ctx)
    app.execute()


if __name__ == '__main__':
    __debug()