import os
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig

from one_dragon.utils import os_utils


class OdStyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    NONE = "none"
    SAMPLE_CARD = "sample_card"
    LINK_CARD = "link_card"
    FLUENT_WINDOW_BASE = "fluent_window_base"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return os.path.join(
            os_utils.get_path_under_work_dir('assets', 'ui', 'qss', theme.value.lower()),
            f"{self.value}.qss"
        )
