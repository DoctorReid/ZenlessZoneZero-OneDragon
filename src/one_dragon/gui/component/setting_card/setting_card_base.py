from PySide6.QtGui import QIcon
from qfluentwidgets import SettingCard, FluentIconBase
from typing import Union

from one_dragon.utils.i18_utils import gt


class SettingCardBase(SettingCard):

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        """
        稍微改造原库里的SettingCard
        """
        SettingCard.__init__(
            self,
            icon=icon,
            title=gt(title, 'ui'),
            parent=parent
        )

        # SettingCard初始化的时候有无content的高度不一致 因此统一不使用构造器传入
        if content is not None:
            self.setContent(gt(content, 'ui'))