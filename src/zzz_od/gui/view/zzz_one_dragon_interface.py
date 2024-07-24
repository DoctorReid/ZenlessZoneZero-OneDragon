from one_dragon.gui.view.one_dragon_interface import OneDragonRunInterface
from zzz_od.application.zzz_one_dragon_app import ZOneDragonApp
from zzz_od.context.zzz_context import ZContext


class ZOneDragonInterface(OneDragonRunInterface):

    def __init__(self, ctx: ZContext, parent=None):
        OneDragonRunInterface.__init__(
            self,
            ctx,
            ZOneDragonApp(ctx),
            parent=parent
        )
