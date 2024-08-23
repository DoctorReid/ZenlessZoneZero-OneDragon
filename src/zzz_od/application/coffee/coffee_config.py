from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class CoffeeChooseWay(Enum):

    PLAN_PRIORITY = ConfigItem('优先体力计划')
    CUSTOM = ConfigItem('只按定制')


class CoffeeChallengeWay(Enum):

    ALL = ConfigItem('全都挑战')
    ONLY_PLAN = ConfigItem('只挑战体力计划')
    NONE = ConfigItem('不挑战')


class CoffeeConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='coffee',
            instance_idx=instance_idx,
        )

    @property
    def choose_way(self) -> str:
        return self.get('choose_way', CoffeeChooseWay.PLAN_PRIORITY.value.value)

    @choose_way.setter
    def choose_way(self, new_value: str) -> None:
        self.update('choose_way', new_value)

    @property
    def challenge_way(self) -> str:
        return self.get('challenge_way', CoffeeChallengeWay.ALL.value.value)

    @challenge_way.setter
    def challenge_way(self, new_value: str) -> None:
        self.update('challenge_way', new_value)

    @property
    def auto_battle(self) -> str:
        return self.get('auto_battle', '击破站场-强攻速切')

    @auto_battle.setter
    def auto_battle(self, new_value: str) -> None:
        self.update('auto_battle', new_value)

    @property
    def day_coffee_1(self) -> str:
        return self.get('day_coffee_1', '新艾利都特调')

    @day_coffee_1.setter
    def day_coffee_1(self, new_value: str) -> None:
        self.update('day_coffee_1', new_value)

    @property
    def day_coffee_2(self) -> str:
        return self.get('day_coffee_2', '新艾利都特调')

    @day_coffee_2.setter
    def day_coffee_2(self, new_value: str) -> None:
        self.update('day_coffee_2', new_value)

    @property
    def day_coffee_3(self) -> str:
        return self.get('day_coffee_3', '新艾利都特调')

    @day_coffee_3.setter
    def day_coffee_3(self, new_value: str) -> None:
        self.update('day_coffee_3', new_value)

    @property
    def day_coffee_4(self) -> str:
        return self.get('day_coffee_4', '新艾利都特调')

    @day_coffee_4.setter
    def day_coffee_4(self, new_value: str) -> None:
        self.update('day_coffee_4', new_value)

    @property
    def day_coffee_5(self) -> str:
        return self.get('day_coffee_5', '新艾利都特调')

    @day_coffee_5.setter
    def day_coffee_5(self, new_value: str) -> None:
        self.update('day_coffee_5', new_value)

    @property
    def day_coffee_6(self) -> str:
        return self.get('day_coffee_6', '新艾利都特调')

    @day_coffee_6.setter
    def day_coffee_6(self, new_value: str) -> None:
        self.update('day_coffee_6', new_value)

    @property
    def day_coffee_7(self) -> str:
        return self.get('day_coffee_7', '新艾利都特调')

    @day_coffee_7.setter
    def day_coffee_7(self, new_value: str) -> None:
        self.update('day_coffee_7', new_value)

    def get_coffee_by_day(self, day: int) -> str:
        """
        根据星期几获取对应的咖啡名称
        :param day: 1~7
        :return:
        """
        if day == 1:
            return self.day_coffee_1
        elif day == 2:
            return self.day_coffee_2
        elif day == 3:
            return self.day_coffee_3
        elif day == 4:
            return self.day_coffee_4
        elif day == 5:
            return self.day_coffee_5
        elif day == 6:
            return self.day_coffee_6
        elif day == 7:
            return self.day_coffee_7
