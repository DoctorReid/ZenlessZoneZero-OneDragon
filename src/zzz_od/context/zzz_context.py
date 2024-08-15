from typing import Optional

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from zzz_od.application.battle_assistant.battle_assistant_config import BattleAssistantConfig
from zzz_od.application.charge_plan.charge_plan_run_record import ChargePlanRunRecord
from zzz_od.application.devtools.screenshot_helper.screenshot_helper_config import ScreenshotHelperConfig
from zzz_od.application.email.email_run_record import EmailRunRecord
from zzz_od.application.engagement_reward.engagement_reward_run_record import EngagementRewardRunRecord
from zzz_od.application.hollow_zero.hollow_zero_config import HollowZeroConfig
from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntConfig
from zzz_od.application.notorious_hunt.notorious_hunt_run_record import NotoriousHuntRunRecord
from zzz_od.application.random_play.random_play_run_record import RandomPlayRunRecord
from zzz_od.application.scratch_card.scratch_card_run_record import ScratchCardRunRecord
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanConfig
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.controller.zzz_pc_controller import ZPcController
from zzz_od.game_data.compendium import CompendiumService
from zzz_od.game_data.map_area import MapAreaService
from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig


class ZContext(OneDragonContext):

    def __init__(self):
        OneDragonContext.__init__(self)

        instance_idx = 0

        # 其它上下文
        from zzz_od.context.battle_context import BattleContext
        self.battle: BattleContext = BattleContext(self)

        from zzz_od.context.battle_dodge_context import BattleDodgeContext
        self.yolo: BattleDodgeContext = BattleDodgeContext(self)

        from zzz_od.context.custom_battle_context import CustomBattleContext
        self.custom_battle: CustomBattleContext = CustomBattleContext(self)

        from zzz_od.context.hollow_context import HollowContext
        self.hollow: HollowContext = HollowContext(self)

        # 基础配置
        self.game_config: GameConfig = GameConfig(instance_idx)

        # 游戏数据
        self.map_service: MapAreaService = MapAreaService()
        self.compendium_service: CompendiumService = CompendiumService()

        # 应用配置
        self.screenshot_helper_config: ScreenshotHelperConfig = ScreenshotHelperConfig(instance_idx)
        self.battle_assistant_config: BattleAssistantConfig = BattleAssistantConfig(instance_idx)
        self.charge_plan_config: ChargePlanConfig = ChargePlanConfig(instance_idx)
        self.notorious_hunt_config: NotoriousHuntConfig = NotoriousHuntConfig(instance_idx)
        self.hollow_zero_config: HollowZeroConfig = HollowZeroConfig(instance_idx)
        self.hollow_zero_challenge_config: Optional[HollowZeroChallengeConfig] = None

        # 运行记录
        game_refresh_hour_offset = self.game_config.game_refresh_hour_offset
        self.email_run_record: EmailRunRecord = EmailRunRecord(instance_idx, game_refresh_hour_offset)
        self.random_play_run_record: RandomPlayRunRecord = RandomPlayRunRecord(instance_idx, game_refresh_hour_offset)
        self.scratch_card_run_record: ScratchCardRunRecord = ScratchCardRunRecord(instance_idx, game_refresh_hour_offset)
        self.charge_plan_run_record: ChargePlanRunRecord = ChargePlanRunRecord(instance_idx, game_refresh_hour_offset)
        self.engagement_reward_run_record: EngagementRewardRunRecord = EngagementRewardRunRecord(instance_idx, game_refresh_hour_offset)
        self.notorious_hunt_record: NotoriousHuntRunRecord = NotoriousHuntRunRecord(instance_idx, game_refresh_hour_offset)

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
                win_title=self.game_config.win_title,
                standard_width=self.project_config.screen_standard_width,
                standard_height=self.project_config.screen_standard_height
            )

        self.hollow.data_service.reload()
        self.init_hollow_config()

    def init_hollow_config(self) -> None:
        """
        对空洞配置进行初始化
        :return:
        """
        challenge_config = self.hollow_zero_config.challenge_config
        if challenge_config is None:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig('', is_mock=True)
        else:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig(challenge_config)
