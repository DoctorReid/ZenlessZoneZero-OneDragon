from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QIcon
from enum import Enum
from qfluentwidgets import SettingCard, FluentIconBase, PushButton
from typing import Union, Iterable, Optional, List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.gui.widgets.setting_card.multi_push_setting_card import MultiPushSettingCard
from one_dragon.utils import yolo_config_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon.utils.yolo_config_utils import is_model_existed
from one_dragon.yolo.onnx_model_loader import OnnxModelLoader
from phosdeiz.gui.widgets import ComboBox


class DownloadRunner(QThread):
    finished = Signal(bool, str)

    def __init__(self, card):
        super().__init__()
        self.card = card

    def run(self):
        """
        运行 最后发送结束信号
        :return:
        """
        try:
            onnx = OnnxModelLoader(
                model_name=self.card.getValue(),
                model_download_url=self.card.model_download_url,
                model_parent_dir_path=yolo_config_utils.get_model_category_dir(self.card.model_sub_dir),
                gh_proxy=self.card.ctx.env_config.is_gh_proxy,
                gh_proxy_url=self.card.ctx.env_config.gh_proxy_url if self.card.ctx.env_config.is_gh_proxy else None,
                personal_proxy=self.card.ctx.env_config.personal_proxy if self.card.ctx.env_config.is_personal_proxy else None,
            )
            self.finished.emit(True, '下载模型成功')
        except Exception:
            self.finished.emit(False, '下载模型失败 请尝试更换代理')


class ModelDownloadSettingCard(MultiPushSettingCard):

    value_changed = Signal(int, object)

    def __init__(self,
                 ctx: OneDragonContext, sub_dir: str, download_url: str,
                 icon: Union[str, QIcon, FluentIconBase], title: str,
                 options_enum: Optional[Iterable[Enum]] = None,
                 options_list: Optional[List[ConfigItem]] = None,
                 content=None, parent=None
                 ):
        """
        :param icon: 左边显示的图标
        :param title: 左边的标题 中文
        :param options_enum: 右侧下拉框的选项
        :param content: 左侧的详细文本 中文
        :param parent: 组件的parent
        """
        self.combo_box = ComboBox()

        if options_enum is not None:
            for opt in options_enum:
                if not isinstance(opt.value, ConfigItem):
                    continue
                opt_item: ConfigItem = opt.value
                self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)
        elif options_list is not None:
            for opt_item in options_list:
                self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

        self.last_index: int = -1  # 上一次选择的下标
        if len(self.combo_box.items) > 0:
            self.combo_box.setCurrentIndex(0)
            self.last_index = 0

        self.combo_box.currentIndexChanged.connect(self._on_index_changed)

        self.download_btn = PushButton(text=gt('下载', 'ui'))
        self.download_btn.clicked.connect(self._on_download_click)

        MultiPushSettingCard.__init__(
            self,
            btn_list=[self.combo_box, self.download_btn],
            icon=icon,
            title=title,
            content=content,
            parent=parent
        )

        self.ctx: OneDragonContext = ctx
        self.model_sub_dir: str = sub_dir
        self.model_download_url: str = download_url
        self._runner: DownloadRunner = DownloadRunner(self)
        self._runner.finished.connect(self._on_download_finish)

    def set_options_by_list(self, options: List[ConfigItem]) -> None:
        """
        设置选项
        :param options:
        :return:
        """
        self.combo_box.setCurrentIndex(-1)
        self.combo_box.clear()
        for opt_item in options:
            self.combo_box.addItem(opt_item.ui_text, userData=opt_item.value)

    def _on_index_changed(self, index: int) -> None:
        """
        值发生改变时 往外发送信号
        :param index:
        :return:
        """
        if index == self.last_index:  # 没改变时 不发送信号
            return
        self.last_index = index
        self.value_changed.emit(index, self.combo_box.itemData(index))

    def setContent(self, content: str) -> None:
        """
        更新左侧详细文本
        :param content: 文本 中文
        :return:
        """
        SettingCard.setContent(self, gt(content, 'ui'))

    def setValue(self, value: object) -> None:
        """
        设置值
        :param value:
        :return:
        """
        for idx, item in enumerate(self.combo_box.items):
            if item.userData == value:
                self.combo_box.setCurrentIndex(idx)
                return

    def getValue(self):
        return self.combo_box.itemData(self.combo_box.currentIndex())

    def check_and_update_display(self) -> None:
        """
        检查模型是否已经存在
        :return:
        """
        if is_model_existed(self.model_sub_dir, self.getValue()):
            self.download_btn.setText(gt('已下载', 'ui'))
            self.download_btn.setDisabled(True)
        else:
            self.download_btn.setText(gt('下载', 'ui'))
            self.download_btn.setDisabled(False)

    def _on_download_click(self) -> None:
        if self._runner.isRunning():
            log.warn('我知道你很急 但你先别急 正在运行了')
            return
        self.download_btn.setText(gt('下载中', 'ui'))
        self.download_btn.setDisabled(False)
        self._runner.start()

    def _on_download_finish(self, result, message):
        log.info(message)
        self.check_and_update_display()