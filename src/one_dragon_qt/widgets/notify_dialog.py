from PySide6.QtWidgets import QWidget, QGridLayout
from qfluentwidgets import MessageBoxBase, SubtitleLabel, CheckBox

from one_dragon.base.operation.one_dragon_context import OneDragonContext


class NotifyDialog(MessageBoxBase):
    """通知配置对话框"""

    def __init__(self, parent=None, ctx=OneDragonContext):
        super().__init__(parent)
        self.ctx: OneDragonContext = ctx

        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")
        
        self.titleLabel = SubtitleLabel("通知设置")
        self.viewLayout.addWidget(self.titleLabel)

        # 存储所有应用的复选框
        self.app_checkboxes = {}

        # 使用网格布局放置复选框
        checkbox_container = QWidget()
        grid_layout = QGridLayout(checkbox_container)
        grid_layout.setContentsMargins(0, 10, 0, 10)
        grid_layout.setSpacing(10)

        app_list = self.ctx.notify_config.app_list
        
        # 每行放置3个复选框
        column_count = 3
        # 使用 enumerate 和 items() 遍历字典获取索引、键和值
        for i, (app_id, app_name) in enumerate(app_list.items()):
            row = i // column_count
            col = i % column_count
            
            # 使用 app_name 作为 CheckBox 的文本
            checkbox = CheckBox(app_name, self)
            initial_checked = getattr(self.ctx.notify_config, app_id, False)
            checkbox.setChecked(initial_checked)
            
            # 保存复选框引用，使用 app_id 作为键
            self.app_checkboxes[app_id] = checkbox
            
            grid_layout.addWidget(checkbox, row, col)
        
        self.viewLayout.addWidget(checkbox_container)

    def accept(self):
        """点击确定时，更新配置"""
        for app_id, checkbox in self.app_checkboxes.items():
            setattr(self.ctx.notify_config, app_id, checkbox.isChecked())
        super().accept()
