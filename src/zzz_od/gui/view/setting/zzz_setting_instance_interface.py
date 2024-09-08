from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.view.setting.setting_instance_interface import SettingInstanceInterface


class ZSettingInstanceInterface(SettingInstanceInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        self.ctx: OneDragonContext = ctx

        SettingInstanceInterface.__init__(
            self,
            ctx=ctx,
            parent=parent
        )