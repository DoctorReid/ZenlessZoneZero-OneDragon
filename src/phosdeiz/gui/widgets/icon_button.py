from PySide6.QtCore import QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    TeachingTip,
    TransparentToolButton,
    TeachingTipTailPosition,
    FluentIconBase,
)
from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class IconButton(TransparentToolButton):
    """包含下拉框的自定义设置卡片类。"""

    icon: Union[str, QIcon, FluentIconBase]
    isTooltip: bool = False
    tip_title: Optional[str] = None
    tip_content: Optional[str] = None
    parent: QWidget = None

    def __post_init__(self):
        """初始化"""
        TransparentToolButton.__init__(self)
        self.setIcon(self.icon)

        # 处理工具提示
        self._tooltip: Optional[TeachingTip] = None
        if self.isTooltip:
            self.installEventFilter(self)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """处理鼠标事件。"""
        if event.type() == QEvent.Type.Enter:
            self._show_tooltip()
        elif event.type() == QEvent.Type.Leave:
            self._hide_tooltip()
        return super().eventFilter(obj, event)

    def _show_tooltip(self) -> None:
        """显示工具提示。"""
        self._tooltip = TeachingTip.create(
            target=self,
            title=self.tip_title,
            content=self.tip_content,
            tailPosition=TeachingTipTailPosition.RIGHT,
            isClosable=False,
            duration=-1,
            parent=self,
        )
        # 设置偏移
        if self._tooltip:
            tooltip_pos = self.mapToGlobal(self.rect().topRight())

            tooltip_pos.setX(tooltip_pos.x() - self._tooltip.size().width() - 40)  # 水平偏移
            tooltip_pos.setY(tooltip_pos.y() - self._tooltip.size().height() / 2 + 35)  # 垂直偏移

            self._tooltip.move(tooltip_pos)

    def _hide_tooltip(self) -> None:
        """隐藏工具提示。"""
        if self._tooltip:
            self._tooltip.close()
            self._tooltip = None

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self is other
