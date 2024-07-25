from one_dragon.base.operation.one_dragon_app import OneDragonApp
from zzz_od.application.email.email_app import EmailApp
from zzz_od.application.random_play.random_play_app import RandomPlayApp
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class ZOneDragonApp(OneDragonApp, ZApplication):

    def __init__(self, ctx: ZContext):
        app_id = 'zzz_one_dragon'
        ZApplication.__init__(self, ctx, app_id)

        app_list = [
            EmailApp(self.ctx),
            RandomPlayApp(self.ctx)
        ]

        OneDragonApp.__init__(self, ctx, app_id, app_list)
