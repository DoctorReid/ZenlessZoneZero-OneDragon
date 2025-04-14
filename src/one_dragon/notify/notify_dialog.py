from PySide6.QtWidgets import QWidget, QGridLayout
from qfluentwidgets import MessageBoxBase, SubtitleLabel, CheckBox

from zzz_od.application.notify.notify_config import NotifyAppList

class NotifyDialog(MessageBoxBase):
    """通知配置对话框"""

    def __init__(self, parent=None, ctx=None):
        super().__init__(parent)

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

        app_list_dict = NotifyAppList.app_list
        
        # 每行放置3个复选框
        column_count = 3
        # 使用 enumerate 和 items() 遍历字典获取索引、键和值
        for i, (app_id, app_name) in enumerate(app_list_dict.items()):
            row = i // column_count
            col = i % column_count
            
            # 使用 app_name 作为 CheckBox 的文本
            checkbox = CheckBox(app_name, self)
            checkbox.setChecked(getattr(ctx.notify_config, f'enable_{app_id}'))
            
            # 保存复选框引用，使用 app_id 作为键
            self.app_checkboxes[app_id] = checkbox
            
            grid_layout.addWidget(checkbox, row, col)
        
        self.viewLayout.addWidget(checkbox_container)
    
    def get_selected_apps(self):
        """获取所有应用的 app_id 及其选中状态的字典"""
        return {app_id: checkbox.isChecked() for app_id, checkbox in self.app_checkboxes.items()}
