from typing import Union

from PySide6.QtGui import Qt, QIcon
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import FluentIconBase, SingleDirectionScrollArea

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.component.interface.base_interface import BaseInterface


class VerticalScrollInterface(BaseInterface):

    def __init__(self, ctx: OneDragonContext, content_widget, object_name: str,
                 nav_text_cn: str, nav_icon: Union[FluentIconBase, QIcon, str] = None,
                 parent=None
                 ):
        """
        垂直方向上可滚动的子页面
        :param content_widget: 内容组件
        :param object_name: 导航用的唯一键
        :param nav_text_cn: 子页面在导航处显示的文本
        :param nav_icon: 子页面在导航处显示的图标
        :param parent:
        """
        BaseInterface.__init__(self, ctx=ctx, object_name=object_name, parent=parent,
                               nav_text_cn=nav_text_cn, nav_icon=nav_icon)
        # 创建一个垂直布局
        main_layout = QVBoxLayout(self)
        scroll_area = SingleDirectionScrollArea(orient=Qt.Orientation.Vertical)
        main_layout.addWidget(scroll_area, stretch=0)

        content_widget.setStyleSheet("QWidget { background-color: transparent; }")
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
