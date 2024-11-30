from one_dragon.base.operation.one_dragon_app import OneDragonApp
from one_dragon.gui.view.one_dragon.one_dragon_run_interface import OneDragonRunInterface
from zzz_od.application.miscellany.miscellany_app import MiscellanyApp
from zzz_od.context.zzz_context import ZContext


class MiscellanyRunInterface(OneDragonRunInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        OneDragonRunInterface.__init__(
            self,
            ctx=ctx,
            nav_text_cn='杂项任务',
            object_name='miscellany_run_interface',
            app_config=ctx.miscellany_config,
            need_multiple_instance=False,
            need_after_done_opt=False,
            parent=parent,
            help_url='https://one-dragon.org/zzz/zh/docs/feat_one_dragon.html'
        )

    def get_one_dragon_app(self) -> OneDragonApp:
        return MiscellanyApp(self.ctx)
