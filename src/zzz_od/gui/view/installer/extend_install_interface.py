from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ProgressBar, IndeterminateProgressBar, SettingCardGroup, \
    FluentIcon

from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.gui.view.installer.gamepad_install_card import GamepadInstallCard


class ExtendInstallInterface(VerticalScrollInterface):

    def __init__(self, ctx: ZContext, parent=None):
        self.ctx: ZContext = ctx
        VerticalScrollInterface.__init__(self, ctx=ctx, object_name='extend_install_interface',
                                         parent=parent, content_widget=None,
                                         nav_text_cn='扩展安装', nav_icon=FluentIcon.DEVELOPER_TOOLS)

    def get_content_widget(self) -> QWidget:
        content_widget = QWidget()
        v_layout = QVBoxLayout(content_widget)

        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setVisible(False)
        v_layout.addWidget(self.progress_bar)

        self.progress_bar_2 = IndeterminateProgressBar()
        self.progress_bar_2.setVisible(False)
        v_layout.addWidget(self.progress_bar_2)

        self.gamepad_opt = GamepadInstallCard(self.ctx)

        update_group = SettingCardGroup(gt('运行环境', 'ui'))
        update_group.addSettingCard(self.gamepad_opt)

        v_layout.addWidget(update_group)

        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        self.log_card = LogDisplayCard()
        log_group.addSettingCard(self.log_card)
        v_layout.addWidget(log_group)

        return content_widget

    def on_interface_shown(self) -> None:
        """
        页面加载完成后 检测各个组件状态并更新显示
        :return:
        """
        VerticalScrollInterface.on_interface_shown(self)
        self.gamepad_opt.check_and_update_display()
        self.log_card.update_on_log = True

    def on_interface_hidden(self) -> None:
        """
        子界面隐藏时的回调
        :return:
        """
        VerticalScrollInterface.on_interface_hidden(self)
        self.log_card.update_on_log = False

    def update_progress(self, progress: float, message: str) -> None:
        """
        进度回调更新
        :param progress: 进度 0~1
        :param message: 当前信息
        :return:
        """
        if progress == -1:
            self.progress_bar.setVisible(False)
            self.progress_bar_2.setVisible(True)
            self.progress_bar_2.start()
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setVal(progress)
            self.progress_bar_2.setVisible(False)
            self.progress_bar_2.stop()

