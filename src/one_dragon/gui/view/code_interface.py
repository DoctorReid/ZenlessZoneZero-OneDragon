from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QWidget, QTableWidgetItem
from qfluentwidgets import TableWidget, PipsPager, FluentIcon, VBoxLayout
from typing import Callable, List

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon.envs.git_service import GitLog
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.setting_card.switch_setting_card import SwitchSettingCard
from one_dragon.gui.install_card.code_install_card import CodeInstallCard
from one_dragon.gui.install_card.git_install_card import GitInstallCard
from one_dragon.gui.install_card.venv_install_card import VenvInstallCard
from one_dragon.utils.i18_utils import gt


class FetchTotalRunner(QThread):

    finished = Signal(int)

    def __init__(self, method: Callable[[], int]):
        super().__init__()
        self.method: Callable[[], int] = method

    def run(self) -> None:
        self.finished.emit(self.method())


class FetchPageRunner(QThread):

    finished = Signal(list)

    def __init__(self, method: Callable[[], List[GitLog]]):
        super().__init__()
        self.method: Callable[[], List[GitLog]] = method

    def run(self) -> None:
        self.finished.emit(self.method())


class CodeInterface(VerticalScrollInterface):

    def __init__(self, ctx: OneDragonEnvContext, parent=None):
        content_widget = QWidget()

        self.page_num: int = -1
        self.page_size: int = 10

        v_layout = VBoxLayout(content_widget)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.force_update_opt = SwitchSettingCard(
            icon=FluentIcon.SYNC, title='强制更新', content='不懂代码请开启，会将脚本更新到最新并将你的改动覆盖，不会使你的配置失效',
        )
        self.force_update_opt.value_changed.connect(self._on_force_update_changed)
        v_layout.addWidget(self.force_update_opt)

        self.git_card = GitInstallCard(ctx)
        self.git_card.install_btn.setDisabled(True)
        self.git_card.finished.connect(self._on_git_updated)
        v_layout.addWidget(self.git_card)

        self.code_card = CodeInstallCard(ctx)
        self.code_card.finished.connect(self.on_code_updated)
        v_layout.addWidget(self.code_card)

        self.venv_card = VenvInstallCard(ctx)
        self.venv_card.install_btn.setDisabled(True)
        v_layout.addWidget(self.venv_card)

        self.log_table = TableWidget()
        self.log_table.setMinimumHeight(self.page_size * 42)

        self.log_table.setBorderVisible(True)
        self.log_table.setBorderRadius(8)

        self.log_table.setWordWrap(True)
        self.log_table.setColumnCount(4)
        self.log_table.setColumnWidth(0, 100)
        self.log_table.setColumnWidth(1, 150)
        self.log_table.setColumnWidth(2, 200)
        self.log_table.setColumnWidth(3, 400)
        self.log_table.verticalHeader().hide()
        self.log_table.setDisabled(True)
        self.log_table.setHorizontalHeaderLabels([
            gt('ID', 'ui'),
            gt('作者', 'ui'),
            gt('时间', 'ui'),
            gt('内容', 'ui')
        ])

        v_layout.addWidget(self.log_table)

        self.pager = PipsPager()
        self.pager.setPageNumber(1)
        self.pager.setVisibleNumber(5)
        self.pager.currentIndexChanged.connect(self.on_page_changed)
        self.pager.setItemAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(self.pager)

        VerticalScrollInterface.__init__(
            self,
            object_name='code_interface',
            parent=parent, content_widget=content_widget,
            nav_text_cn='代码同步', nav_icon=FluentIcon.SYNC
        )
        self.ctx: OneDragonEnvContext = ctx

        self.fetch_total_runner = FetchTotalRunner(ctx.git_service.fetch_total_commit)
        self.fetch_total_runner.finished.connect(self.update_total)
        self.fetch_page_runner = FetchPageRunner(self.fetch_page)
        self.fetch_page_runner.finished.connect(self.update_page)

    def on_interface_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self.force_update_opt.setValue(self.ctx.env_config.force_update)
        self.start_fetch_total()
        self.git_card.check_and_update_display()
        self.code_card.check_and_update_display()
        self.venv_card.check_and_update_display()

    def start_fetch_total(self) -> None:
        """
        开始获取总数
        :return:
        """
        if self.fetch_total_runner.isRunning():
            return
        self.fetch_total_runner.start()

    def update_total(self, total: int) -> None:
        """
        更新总数
        :param total:
        :return:
        """
        self.pager.setPageNumber(total // self.page_size + 1)
        if self.page_num == -1:  # 还没有加载过任何分页
            self.page_num = 0
            self.start_fetch_page()

    def start_fetch_page(self) -> None:
        """
        开始获取分页内容
        :return:
        """
        if self.fetch_page_runner.isRunning():
            return
        self.fetch_page_runner.start()

    def fetch_page(self) -> List[GitLog]:
        """
        获取分页数据
        :return:
        """
        return self.ctx.git_service.fetch_page_commit(self.page_num, self.page_size)

    def update_page(self, log_list: List[GitLog]) -> None:
        """
        更新分页内容
        :param log_list:
        :return:
        """
        page_size = len(log_list)
        self.log_table.setRowCount(page_size)

        for i in range(page_size):
            self.log_table.setItem(i, 0, QTableWidgetItem(log_list[i].commit_id))
            self.log_table.setItem(i, 1, QTableWidgetItem(log_list[i].author))
            self.log_table.setItem(i, 2, QTableWidgetItem(log_list[i].commit_time))
            self.log_table.setItem(i, 3, QTableWidgetItem(log_list[i].commit_message))

    def on_page_changed(self, page: int) -> None:
        """
        翻页
        :param page:
        :return:
        """
        if page == self.page_num:
            return
        self.page_num = page
        self.start_fetch_page()

    def _on_git_updated(self, success: bool) -> None:
        """
        Git选择后更新显示
        :param success: 是否成功
        :return:
        """
        if not success:
            return
        self.git_card.check_and_update_display()
        self.code_card.check_and_update_display()

    def on_code_updated(self, success: bool) -> None:
        """
        代码同步后更新显示
        :param success: 是否成功
        :return:
        """
        if not success:
            return

        self.venv_card.check_and_update_display()
        self.pager.setCurrentIndex(0)
        self.page_num = -1
        self.start_fetch_total()

    def _on_force_update_changed(self, value: bool) -> None:
        self.ctx.env_config.force_update = value
