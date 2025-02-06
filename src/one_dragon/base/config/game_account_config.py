from enum import Enum
from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class GamePlatformEnum(Enum):

    PC = ConfigItem('PC')


class GameLanguageEnum(Enum):

    CN = ConfigItem('简体中文', 'cn')
    EN = ConfigItem('English', 'en')


class GameRegionEnum(Enum):

    CN = ConfigItem('国服/B服', 'cn')
    INTERNATIONAL = ConfigItem('国际服', 'international')


class GameAccountConfig(YamlConfig):

    def __init__(self, instance_idx: int,
                 default_platform: Optional[str] = None,
                 default_game_region: Optional[str] = None,
                 default_game_path: Optional[str] = None,
                 default_account: Optional[str] = None,
                 default_password: Optional[str] = None,
                 ):
        YamlConfig.__init__(self, 'game_account', instance_idx=instance_idx)

        # 迁移的时候 使用旧数据作为默认值
        self.default_platform: str = default_platform
        self.default_game_region: str = default_game_region
        self.default_game_path: str = default_game_path
        self.default_account: str = default_account
        self.default_password: str = default_password

    @property
    def platform(self) -> str:
        return self.get('platform',
                        GamePlatformEnum.PC.value.value if self.default_platform is None else self.default_platform)

    @platform.setter
    def platform(self, new_value: str) -> None:
        self.update('platform', new_value)

    @property
    def game_region(self) -> str:
        return self.get('game_region',
                        GameRegionEnum.CN.value.value if self.default_game_region is None else self.default_game_region)

    @game_region.setter
    def game_region(self, new_value: str) -> None:
        self.update('game_region', new_value)

    @property
    def game_path(self) -> str:
        return self.get('game_path',
                        '' if self.default_game_path is None else self.default_game_path)

    @game_path.setter
    def game_path(self, new_value: str) -> None:
        self.update('game_path', new_value)

    @property
    def game_language(self) -> str:
        return self.get('game_language', GameLanguageEnum.CN.value.value)

    @game_language.setter
    def game_language(self, new_value: str) -> None:
        self.update('game_language', new_value)

    @property
    def account(self) -> str:
        return self.get('account',
                        '' if self.default_account is None else self.default_account)

    @account.setter
    def account(self, new_value: str) -> None:
        self.update('account', new_value)

    @property
    def password(self) -> str:
        return self.get('password',
                        '' if self.default_password is None else self.default_password)

    @password.setter
    def password(self, new_value: str) -> None:
        self.update('password', new_value)

    @property
    def game_refresh_hour_offset(self) -> int:
        if self.game_region == GameRegionEnum.CN.value.value:
            return 4
        elif self.game_region == GameRegionEnum.INTERNATIONAL.value.value:
            return 4
        return 4
