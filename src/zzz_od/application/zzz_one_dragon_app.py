from one_dragon.base.operation.one_dragon_app import OneDragonApp
from zzz_od.application.charge_plan.charge_plan_app import ChargePlanApp
from zzz_od.application.email.email_app import EmailApp
from zzz_od.application.engagement_reward.engagement_reward_app import EngagementRewardApp
from zzz_od.application.notorious_hunt.notorious_hunt_app import NotoriousHuntApp
from zzz_od.application.random_play.random_play_app import RandomPlayApp
from zzz_od.application.scratch_card.scratch_card_app import ScratchCardApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class ZOneDragonApp(OneDragonApp, ZApplication):

    def __init__(self, ctx: ZContext):
        app_id = 'zzz_one_dragon'
        ZApplication.__init__(self, ctx, app_id)

        app_list = [
            EmailApp(self.ctx),
            RandomPlayApp(self.ctx),
            ScratchCardApp(self.ctx),
            ChargePlanApp(self.ctx),
            NotoriousHuntApp(self.ctx),
            EngagementRewardApp(self.ctx),
        ]

        OneDragonApp.__init__(self, ctx, app_id, app_list)
