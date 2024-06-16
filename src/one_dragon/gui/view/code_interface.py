from typing import Callable, List

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem
from qfluentwidgets import SingleDirectionScrollArea, ProgressBar, IndeterminateProgressBar, SettingCardGroup, \
    HeaderCardWidget, TableWidget, PipsPager

from one_dragon.envs.env_config import EnvConfig, env_config
from one_dragon.envs.git_service import GitLog, git_service
from one_dragon.envs.project_config import ProjectConfig, project_config
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.gui.component.od_setting_card import MultiPushSettingCard
from one_dragon.gui.install_card.all_install_card import AllInstallCard
from one_dragon.gui.install_card.code_install_card import CodeInstallCard
from one_dragon.gui.install_card.git_install_card import GitInstallCard
from one_dragon.gui.install_card.pip_install_card import PipInstallCard
from one_dragon.gui.install_card.python_install_card import PythonInstallCard
from one_dragon.gui.install_card.venv_install_card import VenvInstallCard
from one_dragon.gui.view.base_interface import BaseInterface
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


class CodeInterface(SingleDirectionScrollArea, BaseInterface):

    def __init__(self, parent=None):
        BaseInterface.__init__(self)
        SingleDirectionScrollArea.__init__(self, parent=parent, orient=Qt.Orientation.Vertical)
        self.setWidgetResizable(True)

        view = QWidget()
        self.setWidget(view)
        self.setStyleSheet("QScrollArea { border: none; }")
        self.setObjectName('code_interface')

        self.page_num: int = -1
        self.page_size: int = 10

        v_layout = QVBoxLayout(view)

        self.install_card = CodeInstallCard()
        self.install_card.finished.connect(self.on_code_updated)
        v_layout.addWidget(self.install_card)

        self.log_table = TableWidget(self)

        self.log_table.setBorderVisible(True)
        self.log_table.setBorderRadius(8)

        self.log_table.setWordWrap(True)
        self.log_table.setColumnCount(4)
        self.log_table.setColumnWidth(0, 100)
        self.log_table.setColumnWidth(1, 150)
        self.log_table.setColumnWidth(2, 200)
        self.log_table.setColumnWidth(3, 400)
        self.log_table.verticalHeader().hide()
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
        v_layout.addWidget(self.pager)

        self.git_service = git_service
        self.fetch_total_runner = FetchTotalRunner(self.git_service.fetch_total_commit)
        self.fetch_total_runner.finished.connect(self.update_total)
        self.fetch_page_runner = FetchPageRunner(self.fetch_page)
        self.fetch_page_runner.finished.connect(self.update_page)

    def init_on_shown(self) -> None:
        """
        子界面显示时 进行初始化
        :return:
        """
        self.start_fetch_total()
        self.install_card.check_and_update_display()

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
        return self.git_service.fetch_page_commit(self.page_num, self.page_size)

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

    def on_code_updated(self, success: bool) -> None:
        """
        代码同步后更新显示
        :param success: 是否成功
        :return:
        """
        if not success:
            return

        self.pager.setCurrentIndex(0)
        self.page_num = -1
        self.start_fetch_total()