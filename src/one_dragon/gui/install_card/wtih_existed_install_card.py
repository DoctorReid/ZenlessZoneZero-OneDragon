from typing import Callable, Optional

from PySide6.QtWidgets import QFileDialog
from qfluentwidgets import FluentIcon, PushButton

from one_dragon.gui.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class WithExistedInstallCard(BaseInstallCard):

    def __init__(self,
                 title_cn: str,
                 install_method: Callable[[Callable[[float, str], None]], bool],
                 install_btn_icon: FluentIcon = FluentIcon.DOWN,
                 install_btn_text_cn: str = '默认安装',
                 content_cn: str = '未安装'):

        self.existed_btn = PushButton(FluentIcon.FOLDER, gt('选择已有', 'ui'))
        self.existed_btn.clicked.connect(self.choose_existed_file)

        super().__init__(title_cn=title_cn,
                         install_method=install_method,
                         install_btn_icon=install_btn_icon,
                         install_btn_text_cn=install_btn_text_cn,
                         content_cn=content_cn,
                         left_widgets=[self.existed_btn])

    def choose_existed_file(self) -> None:
        """
        选择已有的环境
        :return:
        """
        default_dir = self.get_existed_os_path()
        file_path, _ = QFileDialog.getOpenFileName(self,
                                                   gt('选择你的', 'ui') + self.title,
                                                   dir=default_dir,
                                                   filter="Exe (*.exe)",
                                                   )
        if file_path is not None and file_path.endswith('.exe'):
            self.on_existed_chosen(file_path)

    def get_existed_os_path(self) -> Optional[str]:
        """
        获取系统环境变量中的路径，由子类自行实现
        :return:
        """
        pass

    def on_existed_chosen(self, file_path: str) -> None:
        """
        选择了本地文件之后的回调，由子类自行实现
        :param file_path: 本地文件的路径
        :return:
        """
        pass

