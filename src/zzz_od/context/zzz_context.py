from typing import Optional

# 导入相关模块和配置文件
from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from zzz_od.application.battle_assistant.battle_assistant_config import BattleAssistantConfig
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanConfig
from zzz_od.application.charge_plan.charge_plan_run_record import ChargePlanRunRecord
from zzz_od.application.city_fund.city_fund_run_record import CityFundRunRecord
from zzz_od.application.coffee.coffee_config import CoffeeConfig
from zzz_od.application.coffee.coffee_run_record import CoffeeRunRecord
from zzz_od.application.devtools.screenshot_helper.screenshot_helper_config import ScreenshotHelperConfig
from zzz_od.application.email.email_run_record import EmailRunRecord
from zzz_od.application.engagement_reward.engagement_reward_run_record import EngagementRewardRunRecord
from zzz_od.application.hollow_zero.hollow_zero_config import HollowZeroConfig
from zzz_od.application.hollow_zero.hollow_zero_run_record import HollowZeroRunRecord
from zzz_od.application.notorious_hunt.notorious_hunt_config import NotoriousHuntConfig
from zzz_od.application.notorious_hunt.notorious_hunt_run_record import NotoriousHuntRunRecord
from zzz_od.application.random_play.random_play_run_record import RandomPlayRunRecord
from zzz_od.application.scratch_card.scratch_card_run_record import ScratchCardRunRecord
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.config.yolo_config import YoloConfig
from zzz_od.controller.zzz_pc_controller import ZPcController
from zzz_od.game_data.compendium import CompendiumService
from zzz_od.game_data.map_area import MapAreaService
from zzz_od.hollow_zero.hollow_zero_challenge_config import HollowZeroChallengeConfig


class ZContext(OneDragonContext):

    def __init__(self, is_installer: bool = False, instance_idx: Optional[int] = None):
        """
        初始化ZContext类，继承自OneDragonContext
        :param is_installer: 是否为安装程序模式，如果是，则不加载某些上下文
        :param instance_idx: 指定的实例索引，用于测试或多实例情况
        """
        OneDragonContext.__init__(self)

        # 设置当前实例索引，如果未提供则默认为0
        self.current_instance_idx = 0 if instance_idx is None else instance_idx

        # 如果是安装模式，则直接返回，跳过初始化其他上下文和配置
        if is_installer:
            return

        # 导入并初始化各类上下文
        from zzz_od.context.battle_context import BattleContext
        self.battle: BattleContext = BattleContext(self)

        from zzz_od.context.battle_dodge_context import BattleDodgeContext
        self.battle_dodge: BattleDodgeContext = BattleDodgeContext(self)

        from zzz_od.context.custom_battle_context import CustomBattleContext
        self.custom_battle: CustomBattleContext = CustomBattleContext(self)

        from zzz_od.context.hollow_context import HollowContext
        self.hollow: HollowContext = HollowContext(self)

        # 初始化基础配置
        self.game_config: GameConfig = GameConfig(self.current_instance_idx)
        self.yolo_config: YoloConfig = YoloConfig()

        # 初始化游戏数据服务
        self.map_service: MapAreaService = MapAreaService()
        self.compendium_service: CompendiumService = CompendiumService()

        # 初始化应用配置
        self.screenshot_helper_config: ScreenshotHelperConfig = ScreenshotHelperConfig(self.current_instance_idx)
        self.battle_assistant_config: BattleAssistantConfig = BattleAssistantConfig(self.current_instance_idx)
        self.charge_plan_config: ChargePlanConfig = ChargePlanConfig(self.current_instance_idx)
        self.notorious_hunt_config: NotoriousHuntConfig = NotoriousHuntConfig(self.current_instance_idx)
        self.hollow_zero_config: HollowZeroConfig = HollowZeroConfig(self.current_instance_idx)
        self.hollow_zero_challenge_config: Optional[HollowZeroChallengeConfig] = None
        self.coffee_config: CoffeeConfig = CoffeeConfig(self.current_instance_idx)

        # 初始化运行记录，按实例索引和游戏刷新时间偏移配置
        game_refresh_hour_offset = self.game_config.game_refresh_hour_offset

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

    def init_by_config(self) -> None:
        """
        根据配置初始化上下文，主要是根据游戏配置进行设置
        """
        OneDragonContext.init_by_config(self)
        
        # 更新默认语言
        i18_utils.update_default_lang(self.game_config.game_language)

        # 如果平台是PC，初始化PC控制器
        if self.game_config.platform == GamePlatformEnum.PC.value.value:
            self.controller = ZPcController(
                game_config=self.game_config,
                win_title=self.game_config.win_title,
                standard_width=self.project_config.screen_standard_width,
                standard_height=self.project_config.screen_standard_height
            )

        # 重新加载空洞的数据服务并初始化相关配置
        self.hollow.data_service.reload()
        self.init_hollow_config()

    def init_hollow_config(self) -> None:
        """
        初始化空洞的挑战配置，如果没有挑战配置，则创建一个模拟的挑战配置
        """
        challenge_config = self.hollow_zero_config.challenge_config
        if challenge_config is None:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig('', is_mock=True)
        else:
            self.hollow_zero_challenge_config = HollowZeroChallengeConfig(challenge_config)
