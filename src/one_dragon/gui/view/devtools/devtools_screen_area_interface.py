import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QFileDialog, QTableWidgetItem
from qfluentwidgets import FluentIcon, ImageLabel, DropDownPushButton, PushButton, TableWidget

from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.base.screen.screen_info import ScreenInfo
from one_dragon.gui.component.column_widget import ColumnWidget
from one_dragon.gui.component.cv2_image import Cv2Image
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.row_widget import RowWidget
from one_dragon.gui.component.setting_card.check_box_setting_card import CheckBoxSettingCard
from one_dragon.gui.component.setting_card.text_setting_card import TextSettingCard
from one_dragon.utils import os_utils, cv2_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class ScreenInfoWorker(QObject):

    value_changed = Signal()


class DevtoolsScreenAreaInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonContext, parent=None):
        content_widget = RowWidget()

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

        self.chosen_screen: ScreenInfo = None
        self._worker = ScreenInfoWorker()
        self._worker.value_changed.connect(self._update_display_by_screen)

    def _init_left_part(self) -> QWidget:
        widget = ColumnWidget()

        btn_row = RowWidget()
        widget.add_widget(btn_row)

        self.existed_dropdown = DropDownPushButton(text=gt('选择已有', 'ui'))
        btn_row.add_widget(self.existed_dropdown)

        self.create_btn = PushButton(text=gt('新建', 'ui'))
        self.create_btn.clicked.connect(self._on_create_clicked)
        btn_row.add_widget(self.create_btn)

        self.save_btn = PushButton(text=gt('保存', 'ui'))
        btn_row.add_widget(self.save_btn)

        self.delete_btn = PushButton(text=gt('删除', 'ui'))
        btn_row.add_widget(self.delete_btn)

        btn_row.add_stretch(1)

        self.choose_image_btn = PushButton(text=gt('选择图片', 'ui'))
        self.choose_image_btn.clicked.connect(self.choose_existed_image)
        widget.add_widget(self.choose_image_btn)

        self.screen_id_opt = TextSettingCard(icon=FluentIcon.HOME, title='画面ID')
        widget.add_widget(self.screen_id_opt)

        self.screen_name_opt = TextSettingCard(icon=FluentIcon.HOME, title='画面名称')
        widget.add_widget(self.screen_name_opt)

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
            gt('操作', 'ui'),
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
        self.image_label.scaledToHeight(self.ctx.project_config.screen_standard_height // 2)

        return self.image_label

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        self._update_display_by_screen()

    def _update_display_by_screen(self) -> None:
        """
        根据画面图片，统一更新界面的显示
        :return:
        """
        chosen = self.chosen_screen is not None

        self.existed_dropdown.setDisabled(chosen)
        self.create_btn.setDisabled(chosen)
        self.save_btn.setDisabled(not chosen)
        self.delete_btn.setDisabled(not chosen)

        self.choose_image_btn.setDisabled(not chosen)
        self.screen_id_opt.setDisabled(not chosen)
        self.screen_name_opt.setDisabled(not chosen)
        self.pc_alt_opt.setDisabled(not chosen)

        self._update_image_display()
        self._update_area_table_display()

    def _update_area_table_display(self):
        """
        更新区域表格的显示
        :return:
        """
        area_list = [] if self.chosen_screen is None else self.chosen_screen.area_list
        area_cnt = len(area_list)
        self.area_table.setRowCount(area_cnt + 1)

        for idx in range(area_cnt):
            area_item = area_list[idx]
            del_btn = PushButton(text=gt('删除', 'ui'))
            self.area_table.setCellWidget(idx, 0, del_btn)
            self.area_table.setItem(idx, 1, QTableWidgetItem(area_item.area_name))
            self.area_table.setItem(idx, 2, QTableWidgetItem(str(area_item.pc_rect)))
            self.area_table.setItem(idx, 3, QTableWidgetItem(area_item.text))
            self.area_table.setItem(idx, 4, QTableWidgetItem(str(area_item.lcs_percent)))
            self.area_table.setItem(idx, 5, QTableWidgetItem(area_item.template_id_display_text))
            self.area_table.setItem(idx, 6, QTableWidgetItem(str(area_item.template_match_threshold)))

        add_btn = PushButton(text=gt('新增', 'ui'))
        self.area_table.setCellWidget(area_cnt, 0, add_btn)
        self.area_table.setItem(area_cnt, 2, QTableWidgetItem(''))
        self.area_table.setItem(area_cnt, 3, QTableWidgetItem(''))
        self.area_table.setItem(area_cnt, 4, QTableWidgetItem(''))
        self.area_table.setItem(area_cnt, 5, QTableWidgetItem(''))
        self.area_table.setItem(area_cnt, 6, QTableWidgetItem(''))

    def _update_image_display(self):
        """
        更新图片显示
        :return:
        """
        image_to_show = None if self.chosen_screen is None else self.chosen_screen.get_image_to_show()
        if image_to_show is not None:
            image = Cv2Image(image_to_show)
            self.image_label.setImage(image)
            self.image_label.setFixedSize(image.width() // 2, image.height() // 2)
        else:
            self.image_label.setImage(None)

    def _on_create_clicked(self):
        """
        创建一个新的
        :return:
        """
        if self.chosen_screen is not None:
            return

        self.chosen_screen = ScreenInfo(create_new=True)
        self._worker.value_changed.emit()

    def choose_existed_image(self) -> None:
        """
        选择已有的环图片
        :return:
        """
        default_dir = os_utils.get_path_under_work_dir('.debug', 'images')
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            gt('选择图片', 'ui'),
            dir=default_dir,
            filter="PNG (*.png)",
        )
        if file_path is not None and file_path.endswith('.png'):
            log.info('选择路径 %s', file_path)
            self._on_image_chosen(os.path.normpath(file_path))

    def _on_image_chosen(self, image_file_path: str) -> None:
        """
        选择图片之后的回调
        :param image_file_path:
        :return:
        """
        if self.chosen_screen is None:
            return

        self.chosen_screen.chosen_screen_image = cv2_utils.read_image(image_file_path)
        self._worker.value_changed.emit()
