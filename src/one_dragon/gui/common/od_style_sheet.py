import os
from enum import Enum
from qfluentwidgets import StyleSheetBase, Theme, qconfig

from one_dragon.utils import os_utils


# 注册样式表
class OniStyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    NONE = "none"
    SAMPLE_CARD = "sample_card"
    LINK_CARD = "link_card"
    GAME_BUTTON = "game_button"
    GAME_DIALOG = "game_dialog"
    NOTICE_CARD = "notice_card"
    PIVOT = "pivot"
    
    #窗口配置
    APP_WINDOW = "app_window"
    STACKED_WIDGET = "stacked_widget"
    TITLE_BAR = "title_bar"
    NAVIGATION_INTERFACE = "navigation_interface"
    AREA_WIDGET = "area_widget"

    def path(self, theme=Theme.AUTO):
            theme = qconfig.theme if theme == Theme.AUTO else theme
            return os.path.join(
                os_utils.get_path_under_work_dir('assets', 'ui', 'qss', theme.value.lower()),
                f"{self.value}.qss"
            )