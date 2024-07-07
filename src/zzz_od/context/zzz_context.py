import logging

from one_dragon.base.operation.context_base import ContextBase
from one_dragon.envs.project_config import ProjectConfig, project_config
from one_dragon.utils import i18_utils, log_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.config.one_dragon_config import OneDragonConfig
from zzz_od.const import game_const
from zzz_od.controller.zzz_pc_controller import PcController


class ZContext(ContextBase):

    def __init__(self):
        ContextBase.__init__(self)

        self.init_all()

    def init_all(self) -> None:
        """
        初始化
        :return:
        """
        self.load_config()
        self.load_others()

    def load_config(self) -> None:
        """
        读取配置
        :return:
        """
        self.project_config: ProjectConfig = project_config
        self.one_dragon_config: OneDragonConfig = OneDragonConfig()
        instance_idx = self.one_dragon_config.instance_idx

        self.game_config: GameConfig = GameConfig(instance_idx)

    def load_others(self) -> None:
        """
        加载需要使用的组件
        :return:
        """
        i18_utils.update_default_lang(self.game_config.game_language)
        log_utils.set_log_level(logging.DEBUG if self.one_dragon_config.is_debug else logging.INFO)

        if self.game_config.platform == GamePlatformEnum.PC.value.value:
            self.controller = PcController(
                win_title=gt(self.project_config.project_name, 'ui'),
                standard_width=game_const.STANDARD_WIDTH,
                standard_height=game_const.STANDARD_HEIGHT
            )
