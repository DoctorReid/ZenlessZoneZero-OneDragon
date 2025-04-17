from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon_qt.view.one_dragon.setting_push_interface import SettingPushInterface


class ZSettingPushInterface(SettingPushInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        SettingPushInterface.__init__(
            self,
            ctx=ctx,
            parent=parent
        )