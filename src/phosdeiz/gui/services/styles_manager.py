from enum import Enum
from qfluentwidgets import StyleSheetBase, Theme, qconfig


# PhosStyleSheet 枚举类，定义样式表类型和路径获取方法
class PhosStyleSheet(StyleSheetBase, Enum):
    """样式表类型枚举"""

    NONE = "none"
    SAMPLE_CARD = "sample_card"
    LINK_CARD = "link_card"
    GAME_BUTTON = "game_button"
    GAME_DIALOG = "game_dialog"
    SHARED_BATTLE_DIALOG = "shared_battle_dialog"
    NOTICE_CARD = "notice_card"
    PIVOT = "pivot"

    # 窗口配置样式
    APP_WINDOW = "app_window"
    STACKED_WIDGET = "stacked_widget"
    TITLE_BAR = "title_bar"
    NAVIGATION_INTERFACE = "navigation_interface"
    AREA_WIDGET = "area_widget"

    def path(self, theme=Theme.AUTO):
        """获取样式表的路径

        根据主题设置获取相应的 `.qss` 文件路径。

        Args:
            theme (Theme): 主题设置，默认为 Theme.AUTO

        Returns:
            str: 样式表文件的路径
        """
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/phosdeiz/qss/{theme.value.lower()}/{self.value}.qss"