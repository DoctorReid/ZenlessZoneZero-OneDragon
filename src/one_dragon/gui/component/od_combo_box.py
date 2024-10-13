from qfluentwidgets import ComboBox
from typing import List, Any

from one_dragon.base.config.config_item import ConfigItem


class OdComboBox(ComboBox):

    def __init__(self, parent=None):
        ComboBox.__init__(self, parent)

    def set_items(self, items: List[ConfigItem], target_value: Any = None) -> None:
        """
        更新选项
        且尽量复用原来的选项
        """
        self.blockSignals(True)

        old_data = self.currentData() if target_value is None else target_value

        old_len = len(self.items)
        new_len = len(items)

        min_len = min(old_len, new_len)

        new_idx: int = -1
        for i in range(min_len):
            self.setItemText(i, items[i].ui_text)
            self.setItemData(i, items[i].value)

            if items[i].value == old_data:
                new_idx = i

        if old_len > new_len:
            for i in range(new_len, old_len):
                self.removeItem(i)

        if new_len > old_len:
            for i in range(old_len, new_len):
                item = items[i]
                self.addItem(item.ui_text, userData=item.value)
                if item.value == old_data:
                    new_idx = i

        self.setCurrentIndex(new_idx)
        self.blockSignals(False)
