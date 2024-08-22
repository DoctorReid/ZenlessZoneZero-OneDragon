from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class CoffeeChooseWay(Enum):

    PLAN_PRIORITY = ConfigItem('优先体力计划')
    CUSTOM = ConfigItem('定制')


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
    def day_coffee_1(self) -> str:
        return self.get('day_coffee_1', '红茶拿提')

    @day_coffee_1.setter
    def day_coffee_1(self, new_value: str) -> None:
        self.update('day_coffee_1', new_value)

    @property
    def day_coffee_2(self) -> str:
        return self.get('day_coffee_2', '月壤魔咔（淡）')

    @day_coffee_2.setter
    def day_coffee_2(self, new_value: str) -> None:
        self.update('day_coffee_2', new_value)

    @property
    def day_coffee_3(self) -> str:
        return self.get('day_coffee_3', '果泡拿提')

    @day_coffee_3.setter
    def day_coffee_3(self, new_value: str) -> None:
        self.update('day_coffee_3', new_value)

    @property
    def day_coffee_4(self) -> str:
        return self.get('day_coffee_4', '红茶拿提')

    @day_coffee_4.setter
    def day_coffee_4(self, new_value: str) -> None:
        self.update('day_coffee_4', new_value)

    @property
    def day_coffee_5(self) -> str:
        return self.get('day_coffee_5', '月壤魔咔（淡）')

    @day_coffee_5.setter
    def day_coffee_5(self, new_value: str) -> None:
        self.update('day_coffee_5', new_value)

    @property
    def day_coffee_6(self) -> str:
        return self.get('day_coffee_6', '果泡拿提')

    @day_coffee_6.setter
    def day_coffee_6(self, new_value: str) -> None:
        self.update('day_coffee_6', new_value)

    @property
    def day_coffee_7(self) -> str:
        return self.get('day_coffee_7', '红茶拿提')

    @day_coffee_7.setter
    def day_coffee_7(self, new_value: str) -> None:
        self.update('day_coffee_7', new_value)