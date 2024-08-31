from one_dragon.base.operation.one_dragon_app import OneDragonApp
from one_dragon.gui.view.one_dragon.one_dragon_run_interface import OneDragonRunInterface
from zzz_od.application.zzz_one_dragon_app import ZOneDragonApp
from zzz_od.context.zzz_context import ZContext


class ZOneDragonRunInterface(OneDragonRunInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        OneDragonRunInterface.__init__(
            self,
            ctx=ctx,
            parent=parent,
        )

    def get_one_dragon_app(self) -> OneDragonApp:
        return ZOneDragonApp(self.ctx)
