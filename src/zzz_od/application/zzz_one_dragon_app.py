from one_dragon.base.operation.one_dragon_app import OneDragonApp
from zzz_od.application.charge_plan.charge_plan_app import ChargePlanApp
from zzz_od.application.city_fund.city_fund_app import CityFundApp
from zzz_od.application.coffee.coffee_app import CoffeeApp
from zzz_od.application.email.email_app import EmailApp
from zzz_od.application.engagement_reward.engagement_reward_app import EngagementRewardApp
from zzz_od.application.notorious_hunt.notorious_hunt_app import NotoriousHuntApp
from zzz_od.application.random_play.random_play_app import RandomPlayApp
from zzz_od.application.scratch_card.scratch_card_app import ScratchCardApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.enter_game.open_and_enter_game import OpenAndEnterGame


class ZOneDragonApp(OneDragonApp, ZApplication):

    def __init__(self, ctx: ZContext):
        app_id = 'zzz_one_dragon'
        op_to_enter_game = OpenAndEnterGame(ctx)
        app_list = [
            EmailApp(ctx),
            RandomPlayApp(ctx),
            ScratchCardApp(ctx),
            CoffeeApp(ctx),
            ChargePlanApp(ctx),
            NotoriousHuntApp(ctx),
            EngagementRewardApp(ctx),
            CityFundApp(ctx),
        ]

        ZApplication.__init__(self, ctx, app_id)
        OneDragonApp.__init__(self, ctx, app_id, app_list, op_to_enter_game=op_to_enter_game)
