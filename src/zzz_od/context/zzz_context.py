from one_dragon.base.operation.context_base import OneDragonContext
from one_dragon.utils import i18_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.config.one_dragon_config import OneDragonConfig
from zzz_od.const import game_const
from zzz_od.controller.zzz_pc_controller import ZPcController


class ZContext(OneDragonContext):

    def __init__(self):
        OneDragonContext.__init__(self)

        self.one_dragon_config: OneDragonConfig = OneDragonConfig()
        instance_idx = self.one_dragon_config.instance_idx

        self.game_config: GameConfig = GameConfig(instance_idx)

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_config.game_language)

        if self.game_config.platform == GamePlatformEnum.PC.value.value:
            self.controller = ZPcController(
                win_title=gt(self.project_config.win_title, 'ui'),
                standard_width=game_const.STANDARD_WIDTH,
                standard_height=game_const.STANDARD_HEIGHT
            )


_global_context: ZContext = None


def get_context() -> ZContext:
    global _global_context
    if _global_context is None:
        _global_context = ZContext()
    return _global_context
