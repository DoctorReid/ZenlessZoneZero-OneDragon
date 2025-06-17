from typing import Optional, TYPE_CHECKING

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from zzz_od.game_data.agent import AgentEnum

if TYPE_CHECKING:
    from zzz_od.context.hollow_context import HollowContext
    from zzz_od.application.hollow_zero.lost_void.context.lost_void_context import LostVoidContext
    from zzz_od.game_data.map_area import MapAreaService
    from zzz_od.game_data.compendium import CompendiumService


class ZContext(OneDragonContext):

    def __init__(self,):
        OneDragonContext.__init__(self)


        # 延迟加载的上下文，只在需要时初始化
        self._hollow_zero_challenge_config = None
        self._hollow: Optional['HollowContext'] = None
        self._lost_void: Optional['LostVoidContext'] = None

        # 延迟加载的服务，只在需要时初始化
        self._map_service: Optional['MapAreaService'] = None
        self._compendium_service: Optional['CompendiumService'] = None

        from zzz_od.config.model_config import ModelConfig
        # 基础配置
        self.model_config: ModelConfig = ModelConfig()

        # 实例独有的配置
        self.load_instance_config()

    @property
    def hollow(self) -> 'HollowContext':
        """懒加载空洞上下文"""
        if self._hollow is None:
            from zzz_od.context.hollow_context import HollowContext
            self._hollow = HollowContext(self)
        return self._hollow

    @property
    def lost_void(self) -> 'LostVoidContext':
        """懒加载迷失之地上下文"""
        if self._lost_void is None:
            from zzz_od.application.hollow_zero.lost_void.context.lost_void_context import LostVoidContext
            self._lost_void = LostVoidContext(self)
        return self._lost_void

    @property
    def map_service(self) -> 'MapAreaService':
        """懒加载地图服务"""
        if self._map_service is None:
            from zzz_od.game_data.map_area import MapAreaService
            self._map_service = MapAreaService()
        return self._map_service

    @property
    def compendium_service(self) -> 'CompendiumService':
        """懒加载图鉴服务"""
        if self._compendium_service is None:
            from zzz_od.game_data.compendium import CompendiumService
            self._compendium_service = CompendiumService()
        return self._compendium_service

    def load_instance_config(self) -> None:
        OneDragonContext.load_instance_config(self)

        # 清理缓存的懒加载配置和运行记录
        self._clear_cached_configs()
        self._clear_cached_run_records()

        # 只加载最基本的核心配置
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

        from zzz_od.config.team_config import TeamConfig
        self.team_config: TeamConfig = TeamConfig(self.current_instance_idx)

        from zzz_od.config.agent_outfit_config import AgentOutfitConfig
        self.agent_outfit_config: AgentOutfitConfig = AgentOutfitConfig(self.current_instance_idx)

        self.init_by_config()

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

        # 延迟这些耗时的初始化操作，在真正需要时才执行
        # self.hollow.data_service.reload()  # 这个很耗时，延迟到需要时加载
        # self.init_hollow_config()  # 延迟加载

        # 代理头像模板初始化
        if self.agent_outfit_config.match_all_outfits:
            self.init_agent_template_id_list()
        else:
            self.init_agent_template_id()

    def init_hollow_config(self) -> None:
        """
        对空洞配置进行初始化
        :return:
        """
        from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig
        challenge_config = self.hollow_zero_config.challenge_config
        if challenge_config is None:
            self._hollow_zero_challenge_config = HollowZeroChallengeConfig('', is_mock=True)
        else:
            self._hollow_zero_challenge_config = HollowZeroChallengeConfig(challenge_config)

    def init_agent_template_id(self) -> None:
        """
        代理人头像模板ID的初始化
        :return:
        """
        AgentEnum.NICOLE.value.template_id_list = [self.agent_outfit_config.nicole]
        AgentEnum.ELLEN.value.template_id_list = [self.agent_outfit_config.ellen]
        AgentEnum.ASTRA_YAO.value.template_id_list = [self.agent_outfit_config.astra_yao]

    def init_agent_template_id_list(self) -> None:
        """
        代理人头像模板ID的初始化
        :return:
        """
        AgentEnum.NICOLE.value.template_id_list = self.agent_outfit_config.nicole_outfit_list
        AgentEnum.ELLEN.value.template_id_list = self.agent_outfit_config.ellen_outfit_list
        AgentEnum.ASTRA_YAO.value.template_id_list = self.agent_outfit_config.astra_yao_outfit_list

    def after_app_shutdown(self) -> None:
        """
        App关闭后进行的操作 关闭一切可能资源操作
        @return:
        """
        OneDragonContext.after_app_shutdown(self)

    # 空洞
    @property
    def hollow_zero_config(self) -> 'HollowZeroConfig':
        """懒加载空洞配置"""
        if not hasattr(self, '_hollow_zero_config'):
            from zzz_od.application.hollow_zero.withered_domain.hollow_zero_config import HollowZeroConfig
            self._hollow_zero_config = HollowZeroConfig(self.current_instance_idx)
        return self._hollow_zero_config

    @property
    def hollow_zero_record(self) -> 'HollowZeroRunRecord':
        """懒加载空洞运行记录"""
        if not hasattr(self, '_hollow_zero_record'):
            from zzz_od.application.hollow_zero.withered_domain.hollow_zero_run_record import HollowZeroRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._hollow_zero_record = HollowZeroRunRecord(self.hollow_zero_config, self.current_instance_idx, game_refresh_hour_offset)
            self._hollow_zero_record.check_and_update_status()
        return self._hollow_zero_record

    @property
    def hollow_zero_challenge_config(self) -> 'HollowZeroChallengeConfig':
        """懒加载空洞挑战配置"""
        if not hasattr(self, '_hollow_zero_challenge_config'):
            self.init_hollow_config()
        return self._hollow_zero_challenge_config

    # 迷失之地
    @property
    def lost_void_config(self) -> 'LostVoidConfig':
        """懒加载迷失之地配置"""
        if not hasattr(self, '_lost_void_config'):
            from zzz_od.application.hollow_zero.lost_void.lost_void_config import LostVoidConfig
            self._lost_void_config = LostVoidConfig(self.current_instance_idx)
        return self._lost_void_config

    @property
    def lost_void_record(self) -> 'LostVoidRunRecord':
        """懒加载迷失之地运行记录"""
        if not hasattr(self, '_lost_void_record'):
            from zzz_od.application.hollow_zero.lost_void.lost_void_run_record import LostVoidRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._lost_void_record = LostVoidRunRecord(self.lost_void_config, self.current_instance_idx, game_refresh_hour_offset)
            self._lost_void_record.check_and_update_status()
        return self._lost_void_record

    # Random Play 录像店
    @property
    def random_play_config(self) -> 'RandomPlayConfig':
        """懒加载RandomPlay配置"""
        if not hasattr(self, '_random_play_config'):
            from zzz_od.application.random_play.random_play_config import RandomPlayConfig
            self._random_play_config = RandomPlayConfig(self.current_instance_idx)
        return self._random_play_config

    @property
    def random_play_run_record(self) -> 'RandomPlayRunRecord':
        """懒加载RandomPlay运行记录"""
        if not hasattr(self, '_random_play_run_record'):
            from zzz_od.application.random_play.random_play_run_record import RandomPlayRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._random_play_run_record = RandomPlayRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._random_play_run_record.check_and_update_status()
        return self._random_play_run_record

    # 体力计划
    @property
    def charge_plan_config(self) -> 'ChargePlanConfig':
        """懒加载体力计划配置"""
        if not hasattr(self, '_charge_plan_config'):
            from zzz_od.application.charge_plan.charge_plan_config import ChargePlanConfig
            self._charge_plan_config = ChargePlanConfig(self.current_instance_idx)
        return self._charge_plan_config

    @property
    def charge_plan_run_record(self) -> 'ChargePlanRunRecord':
        """懒加载体力计划运行记录"""
        if not hasattr(self, '_charge_plan_run_record'):
            from zzz_od.application.charge_plan.charge_plan_run_record import ChargePlanRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._charge_plan_run_record = ChargePlanRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._charge_plan_run_record.check_and_update_status()
        return self._charge_plan_run_record

    # 恶名狩猎
    @property
    def notorious_hunt_config(self) -> 'NotoriousHuntConfig':
        """懒加载恶名狩猎配置"""
        if not hasattr(self, '_notorious_hunt_config'):
            from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntConfig
            self._notorious_hunt_config = NotoriousHuntConfig(self.current_instance_idx)
        return self._notorious_hunt_config

    @property
    def notorious_hunt_record(self) -> 'NotoriousHuntRunRecord':
        """懒加载恶名狩猎运行记录"""
        if not hasattr(self, '_notorious_hunt_record'):
            from zzz_od.application.notorious_hunt.notorious_hunt_run_record import NotoriousHuntRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._notorious_hunt_record = NotoriousHuntRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._notorious_hunt_record.check_and_update_status()
        return self._notorious_hunt_record

    # 咖啡计划
    @property
    def coffee_config(self) -> 'CoffeeConfig':
        """懒加载咖啡配置"""
        if not hasattr(self, '_coffee_config'):
            from zzz_od.application.coffee.coffee_config import CoffeeConfig
            self._coffee_config = CoffeeConfig(self.current_instance_idx)
        return self._coffee_config

    @property
    def coffee_record(self) -> 'CoffeeRunRecord':
        """懒加载咖啡运行记录"""
        if not hasattr(self, '_coffee_record'):
            from zzz_od.application.coffee.coffee_run_record import CoffeeRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._coffee_record = CoffeeRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._coffee_record.check_and_update_status()
        return self._coffee_record

    # 拿命验收
    @property
    def life_on_line_config(self) -> 'LifeOnLineConfig':
        """懒加载拿命验收配置"""
        if not hasattr(self, '_life_on_line_config'):
            from zzz_od.application.life_on_line.life_on_line_config import LifeOnLineConfig
            self._life_on_line_config = LifeOnLineConfig(self.current_instance_idx)
        return self._life_on_line_config

    @property
    def life_on_line_record(self) -> 'LifeOnLineRunRecord':
        """懒加载拿命验收运行记录"""
        if not hasattr(self, '_life_on_line_record'):
            from zzz_od.application.life_on_line.life_on_line_run_record import LifeOnLineRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._life_on_line_record = LifeOnLineRunRecord(self.life_on_line_config, self.current_instance_idx, game_refresh_hour_offset)
            self._life_on_line_record.check_and_update_status()
        return self._life_on_line_record

    # 式舆
    @property
    def shiyu_defense_config(self) -> 'ShiyuDefenseConfig':
        """懒加载式舆防卫战配置"""
        if not hasattr(self, '_shiyu_defense_config'):
            from zzz_od.application.shiyu_defense.shiyu_defense_config import ShiyuDefenseConfig
            self._shiyu_defense_config = ShiyuDefenseConfig(self.current_instance_idx)
        return self._shiyu_defense_config

    @property
    def shiyu_defense_record(self) -> 'ShiyuDefenseRunRecord':
        """懒加载式舆防卫战运行记录"""
        if not hasattr(self, '_shiyu_defense_record'):
            from zzz_od.application.shiyu_defense.shiyu_defense_run_record import ShiyuDefenseRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._shiyu_defense_record = ShiyuDefenseRunRecord(self.shiyu_defense_config, self.current_instance_idx, game_refresh_hour_offset)
            self._shiyu_defense_record.check_and_update_status()
        return self._shiyu_defense_record

    # 杂项
    @property
    def miscellany_config(self) -> 'MiscellanyConfig':
        """懒加载杂项配置"""
        if not hasattr(self, '_miscellany_config'):
            from zzz_od.application.miscellany.miscellany_config import MiscellanyConfig
            self._miscellany_config = MiscellanyConfig(self.current_instance_idx)
        return self._miscellany_config

    @property
    def miscellany_record(self) -> 'MiscellanyRunRecord':
        """懒加载杂项运行记录"""
        if not hasattr(self, '_miscellany_record'):
            from zzz_od.application.miscellany.miscellany_run_record import MiscellanyRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._miscellany_record = MiscellanyRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._miscellany_record.check_and_update_status()
        return self._miscellany_record

    # 驱动盘拆解
    @property
    def drive_disc_dismantle_config(self) -> 'DriveDiscDismantleConfig':
        """懒加载驱动盘拆解配置"""
        if not hasattr(self, '_drive_disc_dismantle_config'):
            from zzz_od.application.drive_disc_dismantle.drive_disc_dismantle_config import DriveDiscDismantleConfig
            self._drive_disc_dismantle_config = DriveDiscDismantleConfig(self.current_instance_idx)
        return self._drive_disc_dismantle_config

    @property
    def drive_disc_dismantle_record(self) -> 'DriveDiscDismantleRunRecord':
        """懒加载驱动盘拆解运行记录"""
        if not hasattr(self, '_drive_disc_dismantle_record'):
            from zzz_od.application.drive_disc_dismantle.drive_disc_dismantle_run_record import DriveDiscDismantleRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._drive_disc_dismantle_record = DriveDiscDismantleRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._drive_disc_dismantle_record.check_and_update_status()
        return self._drive_disc_dismantle_record

    # 通知
    @property
    def notify_config(self) -> 'NotifyConfig':
        """懒加载通知配置"""
        if not hasattr(self, '_notify_config'):
            from zzz_od.config.notify_config import NotifyConfig
            self._notify_config = NotifyConfig(self.current_instance_idx)
        return self._notify_config

    @property
    def notify_record(self) -> 'NotifyRunRecord':
        """懒加载通知运行记录"""
        if not hasattr(self, '_notify_record'):
            from zzz_od.application.notify.notify_run_record import NotifyRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._notify_record = NotifyRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._notify_record.check_and_update_status()
        return self._notify_record

    # 工具类配置
    @property
    def battle_assistant_config(self) -> 'BattleAssistantConfig':
        """懒加载战斗助手配置"""
        if not hasattr(self, '_battle_assistant_config'):
            from zzz_od.application.battle_assistant.battle_assistant_config import BattleAssistantConfig
            self._battle_assistant_config = BattleAssistantConfig(self.current_instance_idx)
        return self._battle_assistant_config

    @property
    def screenshot_helper_config(self) -> 'ScreenshotHelperConfig':
        """懒加载截图助手配置"""
        if not hasattr(self, '_screenshot_helper_config'):
            from zzz_od.application.devtools.screenshot_helper.screenshot_helper_config import ScreenshotHelperConfig
            self._screenshot_helper_config = ScreenshotHelperConfig(self.current_instance_idx)
        return self._screenshot_helper_config

    @property
    def commission_assistant_config(self) -> 'CommissionAssistantConfig':
        """懒加载委托助手配置"""
        if not hasattr(self, '_commission_assistant_config'):
            from zzz_od.application.commission_assistant.commission_assistant_config import CommissionAssistantConfig
            self._commission_assistant_config = CommissionAssistantConfig(self.current_instance_idx)
        return self._commission_assistant_config

    # 日常任务
    @property
    def email_run_record(self) -> 'EmailRunRecord':
        """懒加载邮件运行记录"""
        if not hasattr(self, '_email_run_record'):
            from zzz_od.application.email_app.email_run_record import EmailRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._email_run_record = EmailRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._email_run_record.check_and_update_status()
        return self._email_run_record

    @property
    def scratch_card_run_record(self) -> 'ScratchCardRunRecord':
        """懒加载刮刮卡运行记录"""
        if not hasattr(self, '_scratch_card_run_record'):
            from zzz_od.application.scratch_card.scratch_card_run_record import ScratchCardRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._scratch_card_run_record = ScratchCardRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._scratch_card_run_record.check_and_update_status()
        return self._scratch_card_run_record

    @property
    def trigrams_collection_record(self) -> 'TrigramsCollectionRunRecord':
        """懒加载卦象集录运行记录"""
        if not hasattr(self, '_trigrams_collection_record'):
            from zzz_od.application.trigrams_collection.trigrams_collection_record import TrigramsCollectionRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._trigrams_collection_record = TrigramsCollectionRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._trigrams_collection_record.check_and_update_status()
        return self._trigrams_collection_record

    @property
    def engagement_reward_run_record(self) -> 'EngagementRewardRunRecord':
        """懒加载活跃度奖励运行记录"""
        if not hasattr(self, '_engagement_reward_run_record'):
            from zzz_od.application.engagement_reward.engagement_reward_run_record import EngagementRewardRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._engagement_reward_run_record = EngagementRewardRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._engagement_reward_run_record.check_and_update_status()
        return self._engagement_reward_run_record

    @property
    def city_fund_record(self) -> 'CityFundRunRecord':
        """懒加载丽都城募运行记录"""
        if not hasattr(self, '_city_fund_record'):
            from zzz_od.application.city_fund.city_fund_run_record import CityFundRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._city_fund_record = CityFundRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._city_fund_record.check_and_update_status()
        return self._city_fund_record

    @property
    def redemption_code_record(self) -> 'RedemptionCodeRunRecord':
        """懒加载兑换码运行记录"""
        if not hasattr(self, '_redemption_code_record'):
            from zzz_od.application.redemption_code.redemption_code_run_record import RedemptionCodeRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._redemption_code_record = RedemptionCodeRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._redemption_code_record.check_and_update_status()
        return self._redemption_code_record

    @property
    def ridu_weekly_record(self) -> 'RiduWeeklyRunRecord':
        """懒加载丽都周纪运行记录"""
        if not hasattr(self, '_ridu_weekly_record'):
            from zzz_od.application.ridu_weekly.ridu_weekly_run_record import RiduWeeklyRunRecord
            game_refresh_hour_offset = self.game_account_config.game_refresh_hour_offset
            self._ridu_weekly_record = RiduWeeklyRunRecord(self.current_instance_idx, game_refresh_hour_offset)
            self._ridu_weekly_record.check_and_update_status()
        return self._ridu_weekly_record

    def _clear_cached_configs(self) -> None:
        """清理所有缓存的配置对象"""
        config_attrs = [
            '_hollow_zero_config',
            '_battle_assistant_config',
            '_screenshot_helper_config',
            '_random_play_config',
            '_commission_assistant_config',
            '_charge_plan_config',
            '_notorious_hunt_config',
            '_coffee_config',
            '_life_on_line_config',
            '_shiyu_defense_config',
            '_miscellany_config',
            '_drive_disc_dismantle_config',
            '_notify_config',
            '_lost_void_config',
            '_hollow_zero_challenge_config'
        ]

        for attr in config_attrs:
            if hasattr(self, attr):
                delattr(self, attr)

    def _clear_cached_run_records(self) -> None:
        """清理所有缓存的运行记录对象"""
        record_attrs = [
            '_email_run_record',
            '_random_play_run_record',
            '_scratch_card_run_record',
            '_charge_plan_run_record',
            '_engagement_reward_run_record',
            '_notorious_hunt_record',
            '_hollow_zero_record',
            '_coffee_record',
            '_city_fund_record',
            '_life_on_line_record',
            '_redemption_code_record',
            '_ridu_weekly_record',
            '_shiyu_defense_record',
            '_miscellany_record',
            '_drive_disc_dismantle_record',
            '_notify_record',
            '_lost_void_record',
            '_trigrams_collection_record'
        ]

        for attr in record_attrs:
            if hasattr(self, attr):
                delattr(self, attr)