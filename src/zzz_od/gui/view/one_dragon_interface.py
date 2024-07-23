from qfluentwidgets import FluentIcon

from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from zzz_od.context.zzz_context import ZContext


class OneDragonInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        content_widget = ColumnWidget()

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            nav_icon=FluentIcon.BUS,
            object_name='one_dragon_interface',
            content_widget=content_widget, parent=parent,
            nav_text_cn='一条龙'
        )
