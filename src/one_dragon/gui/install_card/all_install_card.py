from typing import List, Callable

from qfluentwidgets import FluentIcon, FluentThemeColor

from one_dragon.envs.env_config import EnvConfig, env_config
from one_dragon.envs.git_service import git_service, GitService
from one_dragon.envs.project_config import ProjectConfig, project_config
from one_dragon.gui.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log


class AllInstallCard(BaseInstallCard):

    def __init__(self, install_cards: List[BaseInstallCard]):
        self.env_config: EnvConfig = env_config
        self.project_config: ProjectConfig = project_config
        self.git_service: GitService = git_service

        self.install_cards: List[BaseInstallCard] = install_cards  # 按顺序进行安装的内容
        self.installing_idx: int = -1  # 正在进行安装的下标

        for card in self.install_cards:
            card.finished.connect(self.on_install_done)

        super().__init__(
            title_cn='全部',
            content_cn='正常情况请使用一件安装。如你了解如何使用个人环境，可在下方选择。',
            install_method=self.install_all,
            install_btn_text_cn='一件安装',
        )

    def install_all(self, progress_callback: Callable[[float, str], None]) -> bool:
        """
        按顺序进行安装
        :return:
        """
        log.info('一键安装 开始')
        self.update_display(None, gt('安装中', 'ui'))
        self.installing_idx = 0
        self.install_cards[self.installing_idx].start_progress()
        return True

    def on_install_done(self, success: bool) -> None:
        """
        一个成功安装后的回调
        :param success:
        :return:
        """
        if self.installing_idx == -1:  # 并非从这里开始的一件安装
            return
        if not success:  # 失败了 重置进度
            self.update_display(None,
                                f"{gt('安装失败', 'ui')} {self.install_cards[self.installing_idx].title}")
            self.installing_idx = -1
        else:
            log.info('一键安装 开始下一个')
            self.installing_idx += 1
            if self.installing_idx < len(self.install_cards):
                self.install_cards[self.installing_idx].start_progress()
            else:
                self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value),
                                    gt('安装成功', 'ui'))
