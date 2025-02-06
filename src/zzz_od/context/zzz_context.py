from typing import Optional

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from zzz_od.game_data.agent import AgentEnum


class ZContext(OneDragonContext):

    def __init__(self,):
        OneDragonContext.__init__(self)

        from zzz_od.context.hollow_context import HollowContext
        self.hollow: HollowContext = HollowContext(self)
        from zzz_od.application.hollow_zero.lost_void.context.lost_void_context import LostVoidContext
        self.lost_void: LostVoidContext = LostVoidContext(self)

        from zzz_od.config.yolo_config import YoloConfig
        from zzz_od.game_data.compendium import CompendiumService
        from zzz_od.game_data.map_area import MapAreaService

        # 基础配置
        self.yolo_config: YoloConfig = YoloConfig()

        # 游戏数据
        self.map_service: MapAreaService = MapAreaService()
        self.compendium_service: CompendiumService = CompendiumService()

        # 实例独有的配置
        self.load_instance_config()

    def load_instance_config(self) -> None:
        OneDragonContext.load_instance_config(self)

        from zzz_od.config.game_config import GameConfig
        self.game_config: GameConfig = GameConfig(self.current_instance_idx)
        from one_dragon.base.config.game_account_config import GameAccountConfig
        self.game_account_config: GameAccountConfig = GameAccountConfig(
            self.current_instance_idx,
            default_platform=self.game_config.get('platform'),  # 迁移旧配置 2025-07 时候删除
            default_game_region=self.game_config.get('game_region'),
            default_game_path=self.game_config.get('game_path'),
            default_account=self.game_config.get('account'),
            default_password=self.game_config.get('password'),
        )

        from zzz_od.application.battle_assistant.battle_assistant_config import BattleAssistantConfig
        from zzz_od.application.charge_plan.charge_plan_config import ChargePlanConfig
        from zzz_od.application.charge_plan.charge_plan_run_record import ChargePlanRunRecord
        from zzz_od.application.city_fund.city_fund_run_record import CityFundRunRecord
        from zzz_od.application.coffee.coffee_config import CoffeeConfig
        from zzz_od.application.coffee.coffee_run_record import CoffeeRunRecord
        from zzz_od.application.devtools.screenshot_helper.screenshot_helper_config import ScreenshotHelperConfig
        from zzz_od.application.email_app.email_run_record import EmailRunRecord
        from zzz_od.application.engagement_reward.engagement_reward_run_record import EngagementRewardRunRecord
        from zzz_od.application.hollow_zero.withered_domain.hollow_zero_config import HollowZeroConfig
        from zzz_od.application.hollow_zero.withered_domain.hollow_zero_run_record import HollowZeroRunRecord
        from zzz_od.application.life_on_line.life_on_line_config import LifeOnLineConfig
        from zzz_od.application.life_on_line.life_on_line_run_record import LifeOnLineRunRecord
        from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntConfig
        from zzz_od.application.notorious_hunt.notorious_hunt_run_record import NotoriousHuntRunRecord
        from zzz_od.application.random_play.random_play_run_record import RandomPlayRunRecord
        from zzz_od.application.scratch_card.scratch_card_run_record import ScratchCardRunRecord
        from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig
        from zzz_od.application.redemption_code.redemption_code_run_record import RedemptionCodeRunRecord
        from zzz_od.application.commission_assistant.commission_assistant_config import CommissionAssistantConfig
        from zzz_od.config.team_config import TeamConfig
        self.team_config: TeamConfig = TeamConfig(self.current_instance_idx)

        # 应用配置
        self.screenshot_helper_config: ScreenshotHelperConfig = ScreenshotHelperConfig(self.current_instance_idx)
        self.battle_assistant_config: BattleAssistantConfig = BattleAssistantConfig(self.current_instance_idx)
        self.charge_plan_config: ChargePlanConfig = ChargePlanConfig(self.current_instance_idx)
        self.notorious_hunt_config: NotoriousHuntConfig = NotoriousHuntConfig(self.current_instance_idx)
        self.hollow_zero_config: HollowZeroConfig = HollowZeroConfig(self.current_instance_idx)
        self.hollow_zero_challenge_config: Optional[HollowZeroChallengeConfig] = None
        self.init_hollow_config()
        self.coffee_config: CoffeeConfig = CoffeeConfig(self.current_instance_idx)
        self.life_on_line_config: LifeOnLineConfig = LifeOnLineConfig(self.current_instance_idx)
        self.commission_assistant_config: CommissionAssistantConfig = CommissionAssistantConfig(self.current_instance_idx)
        from zzz_od.application.random_play.random_play_config import RandomPlayConfig
        self.random_play_config: RandomPlayConfig = RandomPlayConfig(self.current_instance_idx)

        from zzz_od.config.agent_outfit_config import AgentOutfitConfig
        self.agent_outfit_config: AgentOutfitConfig = AgentOutfitConfig(self.current_instance_idx)

        # 运行记录
        game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
        self.email_run_record: EmailRunRecord = EmailRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.email_run_record.check_and_update_status()
        self.random_play_run_record: RandomPlayRunRecord = RandomPlayRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.random_play_run_record.check_and_update_status()
        self.scratch_card_run_record: ScratchCardRunRecord = ScratchCardRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.scratch_card_run_record.check_and_update_status()
        self.charge_plan_run_record: ChargePlanRunRecord = ChargePlanRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.charge_plan_run_record.check_and_update_status()
        self.engagement_reward_run_record: EngagementRewardRunRecord = EngagementRewardRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.engagement_reward_run_record.check_and_update_status()
        self.notorious_hunt_record: NotoriousHuntRunRecord = NotoriousHuntRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.notorious_hunt_record.check_and_update_status()
        self.hollow_zero_record: HollowZeroRunRecord = HollowZeroRunRecord(self.hollow_zero_config, self.current_instance_idx, game_refresh_hour_offset)
        self.hollow_zero_record.check_and_update_status()
        self.coffee_record: CoffeeRunRecord = CoffeeRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.coffee_record.check_and_update_status()
        self.city_fund_record: CityFundRunRecord = CityFundRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.city_fund_record.check_and_update_status()
        self.life_on_line_record: LifeOnLineRunRecord = LifeOnLineRunRecord(self.life_on_line_config, self.current_instance_idx, game_refresh_hour_offset)
        self.life_on_line_record.check_and_update_status()
        self.redemption_code_record: RedemptionCodeRunRecord = RedemptionCodeRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.redemption_code_record.check_and_update_status()

        from zzz_od.application.ridu_weekly.ridu_weekly_run_record import RiduWeeklyRunRecord
        self.ridu_weekly_record: RiduWeeklyRunRecord = RiduWeeklyRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        self.ridu_weekly_record.check_and_update_status()

        from zzz_od.application.shiyu_defense.shiyu_defense_config import ShiyuDefenseConfig
        self.shiyu_defense_config: ShiyuDefenseConfig = ShiyuDefenseConfig(self.current_instance_idx)
        from zzz_od.application.shiyu_defense.shiyu_defense_run_record import ShiyuDefenseRunRecord
        self.shiyu_defense_record: ShiyuDefenseRunRecord = ShiyuDefenseRunRecord(self.shiyu_defense_config, self.current_instance_idx, game_refresh_hour_offset)

        from zzz_od.application.miscellany.miscellany_run_record import MiscellanyRunRecord
        self.miscellany_record: MiscellanyRunRecord = MiscellanyRunRecord(self.current_instance_idx, game_refresh_hour_offset)
        from zzz_od.application.miscellany.miscellany_config import MiscellanyConfig
        self.miscellany_config: MiscellanyConfig = MiscellanyConfig(self.current_instance_idx)

        from zzz_od.application.drive_disc_dismantle.drive_disc_dismantle_config import DriveDiscDismantleConfig
        self.drive_disc_dismantle_config: DriveDiscDismantleConfig = DriveDiscDismantleConfig(self.current_instance_idx)
        from zzz_od.application.drive_disc_dismantle.drive_disc_dismantle_run_record import DriveDiscDismantleRunRecord
        self.drive_disc_dismantle_record: DriveDiscDismantleRunRecord = DriveDiscDismantleRunRecord(self.current_instance_idx, game_refresh_hour_offset)

        from zzz_od.application.hollow_zero.lost_void.lost_void_config import LostVoidConfig
        self.lost_void_config: LostVoidConfig = LostVoidConfig(self.current_instance_idx)
        from zzz_od.application.hollow_zero.lost_void.lost_void_run_record import LostVoidRunRecord
        self.lost_void_record: LostVoidRunRecord = LostVoidRunRecord(self.lost_void_config, self.current_instance_idx, game_refresh_hour_offset)

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_account_config.game_language)

        from zzz_od.controller.zzz_pc_controller import ZPcController
        from one_dragon.base.config.game_account_config import GamePlatformEnum
        if self.game_account_config.platform == GamePlatformEnum.PC.value.value:
            from one_dragon.base.config.game_account_config import GameRegionEnum
            win_title = '绝区零' if self.game_account_config.game_region == GameRegionEnum.CN.value.value else 'ZenlessZoneZero'
            self.controller = ZPcController(
                game_config=self.game_config,
                win_title=win_title,
                standard_width=self.project_config.screen_standard_width,
                standard_height=self.project_config.screen_standard_height
            )

        self.hollow.data_service.reload()
        self.init_hollow_config()
        self.init_agent_template_id()

    def init_hollow_config(self) -> None:
        """
        对空洞配置进行初始化
        :return:
        """
        from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig
        challenge_config = self.hollow_zero_config.challenge_config
        if challenge_config is None:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig('', is_mock=True)
        else:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig(challenge_config)

    def init_agent_template_id(self) -> None:
        """
        代理人头像模板ID的初始化
        :return:
        """
        AgentEnum.NICOLE.value.template_id = self.agent_outfit_config.nicole
        AgentEnum.ELLEN.value.template_id = self.agent_outfit_config.ellen
        AgentEnum.ASTRA_YAO.value.template_id = self.agent_outfit_config.astra_yao

    def after_app_shutdown(self) -> None:
        """
        App关闭后进行的操作 关闭一切可能资源操作
        @return:
        """
        OneDragonContext.after_app_shutdown(self)
