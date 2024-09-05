from typing import List

from one_dragon.base.operation.one_dragon_app import OneDragonApp
from zzz_od.application.charge_plan.charge_plan_app import ChargePlanApp
from zzz_od.application.city_fund.city_fund_app import CityFundApp
from zzz_od.application.coffee.coffee_app import CoffeeApp
from zzz_od.application.email_app.email_app import EmailApp
from zzz_od.application.engagement_reward.engagement_reward_app import EngagementRewardApp
from zzz_od.application.notorious_hunt.notorious_hunt_app import NotoriousHuntApp
from zzz_od.application.random_play.random_play_app import RandomPlayApp
from zzz_od.application.scratch_card.scratch_card_app import ScratchCardApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.enter_game.open_and_enter_game import OpenAndEnterGame
from zzz_od.operation.enter_game.switch_account import SwitchAccount


class ZOneDragonApp(OneDragonApp, ZApplication):

    def __init__(self, ctx: ZContext):
        app_id = 'zzz_one_dragon'
        op_to_enter_game = OpenAndEnterGame(ctx)
        op_to_switch_account = SwitchAccount(ctx)

        ZApplication.__init__(self, ctx, app_id)
        OneDragonApp.__init__(self, ctx, app_id,
                              op_to_enter_game=op_to_enter_game,
                              op_to_switch_account=op_to_switch_account)

    def get_app_list(self) -> List[ZApplication]:
        return [
            EmailApp(self.ctx),
            RandomPlayApp(self.ctx),
            ScratchCardApp(self.ctx),
            CoffeeApp(self.ctx),
            ChargePlanApp(self.ctx),
            NotoriousHuntApp(self.ctx),
            EngagementRewardApp(self.ctx),
            CityFundApp(self.ctx),
        ]


def __debug():
    ctx = ZContext()
    ctx.init_by_config()

    app = ZOneDragonApp(ctx)
    app.execute()

    from one_dragon.base.config.one_dragon_config import AfterDoneOpEnum
    if ctx.one_dragon_config.after_done == AfterDoneOpEnum.SHUTDOWN.value.value:
        from one_dragon.utils import cmd_utils
        cmd_utils.shutdown_sys(60)
    elif ctx.one_dragon_config.after_done == AfterDoneOpEnum.CLOSE_GAME.value.value:
        ctx.controller.close_game()


if __name__ == '__main__':
    __debug()