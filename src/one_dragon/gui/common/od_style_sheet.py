from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig


# 样式表列表
OdStyleSheetList = []

# 注册样式表
class OdStyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    NONE = "none"
    SAMPLE_CARD = "sample_card"
    LINK_CARD = "link_card"
    
    #窗口配置
    APP_WINDOW = "app_window"
    STACKED_WIDGET = "stacked_widget"
    TITLE_BAR = "title_bar"
    NAVIGATION_INTERFACE = "navigation_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"./assets/ui/qss/{theme.value.lower()}/{self.value}.qss"