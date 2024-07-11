from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.utils import i18_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.dodge_assistant.dodge_assistant_config import DodgeAssistantConfig
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.config.one_dragon_config import OneDragonConfig
from zzz_od.context.yolo_context import YoloContext
from zzz_od.controller.zzz_pc_controller import ZPcController


class ZContext(OneDragonContext, YoloContext):

    def __init__(self):
        OneDragonContext.__init__(self)
        YoloContext.__init__(self)

        self.one_dragon_config: OneDragonConfig = OneDragonConfig()

        self.init_instance_config()

    def init_instance_config(self) -> None:
        """
        按实例初始化配置
        :return:
        """
        instance_idx = self.one_dragon_config.instance_idx

        # 基础配置
        self.game_config: GameConfig = GameConfig(instance_idx)

        # 应用配置
        self.dodge_assistant_config: DodgeAssistantConfig = DodgeAssistantConfig(instance_idx)

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_config.game_language)

        if self.game_config.platform == GamePlatformEnum.PC.value.value:
            self.controller = ZPcController(
                game_config=self.game_config,
                win_title=gt(self.project_config.win_title, 'ui'),
                standard_width=self.project_config.screen_standard_width,
                standard_height=self.project_config.screen_standard_height
            )
