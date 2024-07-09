import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QFileDialog, QVBoxLayout
from qfluentwidgets import FluentIcon, ImageLabel, PrimaryPushButton, DropDownPushButton, PushButton, LineEdit, \
    CaptionLabel, CheckBox, TableWidget

from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.gui.component.setting_card.check_box_setting_card import CheckBoxSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils import debug_utils, os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class DevtoolsScreenAreaInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        content_widget = RowWidget()
        # content_widget.row_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        VerticalScrollInterface.__init__(
            self,
            ctx=ctx,
            content_widget=content_widget,
            object_name='devtools_screen_area_interface',
            parent=parent,
            nav_text_cn='画面管理'
        )

        content_widget.add_widget(self._init_left_part())
        content_widget.add_widget(self._init_right_part())

    def _init_left_part(self) -> QWidget:
        widget = ColumnWidget()

        btn_row = RowWidget()
        widget.add_widget(btn_row)

        self.existed_dropdown = DropDownPushButton(text=gt('选择已有', 'ui'))
        btn_row.add_widget(self.existed_dropdown)

        self.create_dropdown = PushButton(text=gt('新建', 'ui'))
        btn_row.add_widget(self.create_dropdown)

        self.save_dropdown = PushButton(text=gt('保存', 'ui'))
        btn_row.add_widget(self.save_dropdown)

        self.delete_dropdown = PushButton(text=gt('删除', 'ui'))
        btn_row.add_widget(self.delete_dropdown)

        btn_row.add_stretch(1)

        self.choose_image_btn = PushButton(text=gt('选择图片', 'ui'))
        widget.add_widget(self.choose_image_btn)

        screen_opt = TextSettingCard(icon=FluentIcon.HOME, title='画面名称')
        widget.add_widget(screen_opt)

        self.pc_alt_opt = CheckBoxSettingCard(icon=FluentIcon.MOVE, title='PC点击需alt')
        widget.add_widget(self.pc_alt_opt)

        self.area_table = TableWidget()
        self.area_table.setMinimumWidth(500)
        self.area_table.setMinimumHeight(420)
        self.area_table.setBorderVisible(True)
        self.area_table.setBorderRadius(8)
        self.area_table.setWordWrap(True)
        self.area_table.setColumnCount(6)
        self.area_table.verticalHeader().hide()
        self.area_table.setHorizontalHeaderLabels([
            gt('区域名称', 'ui'),
            gt('位置', 'ui'),
            gt('文本', 'ui'),
            gt('文本阈值', 'ui'),
            gt('模板', 'ui'),
            gt('模板阈值', 'ui')
        ])
        widget.add_widget(self.area_table)

        widget.add_stretch(1)
        return widget

    def _init_right_part(self) -> QWidget:
        self.image_label = ImageLabel()
        self.image_label.setImage(debug_utils.get_debug_image_path('switch_1720365982348'))
        self.image_label.scaledToHeight(self.ctx.project_config.screen_standard_height // 2)

        return self.image_label

    def choose_existed_file(self) -> None:
        """
        选择已有的环图片
        :return:
        """
        default_dir = os_utils.get_path_under_work_dir('assets', 'screen_area', 'images')
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            gt('选择图片', 'ui'),
            dir=default_dir,
            filter="PNG (*.png)",
        )
        if file_path is not None and file_path.endswith('.exe'):
            log.info('选择路径 %s', file_path)
            self.on_existed_chosen(os.path.normpath(file_path))
