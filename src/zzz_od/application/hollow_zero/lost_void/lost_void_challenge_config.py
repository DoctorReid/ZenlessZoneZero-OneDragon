from enum import Enum

from one_dragon.base.config.config_item import ConfigItem


class LostVoidRegionType(Enum):
    """
    注意需要和识别模型的结果名称一致
    """

    ENTRY = ConfigItem('入口')
    COMBAT_RESONIUM = ConfigItem('战斗-鸣徽')
    COMBAT_GEAR = ConfigItem('战斗-武备')
    COMBAT_COIN = ConfigItem('战斗-硬币')
    CHANLLENGE_FLAWLESS = ConfigItem('挑战-无伤')
    CHANLLENGE_TIME_TRAIL = ConfigItem('挑战-限时')
    ENCOUNTER = ConfigItem('偶遇事件')
    PRICE_DIFFERENCE = ConfigItem('代价之间')
    REST = ConfigItem('休憩调息')
    BANGBOO_STORE = ConfigItem('邦布商店')
    FRIENDLY_TALK = ConfigItem('挚交会谈')
    ELITE = ConfigItem('战斗-道中危机')
    BOSS = ConfigItem('战斗-终结之役')
