import os
from typing import List

from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


class HollowZeroChallengeConfig(YamlConfig):

    def __init__(self, module_name: str, is_mock: bool = False):
        YamlConfig.__init__(
            self,
            module_name,
            sub_dir=['hollow_zero_challenge'],
            is_mock=is_mock, sample=False
        )

        self.old_module_name: str = self.module_name
        self.old_file_path: str = self.file_path

    def copy_new(self) -> None:
        """
        复制变成一个新的
        :return:
        """
        self.module_name = self.module_name + '_copy'

        self.file_path = self._get_yaml_file_path()

    def save(self) -> None:
        if self.old_module_name != self.module_name:
            # 删除旧文件
            os.remove(self.old_file_path)
            self.file_path = self._get_yaml_file_path()

        self.old_module_name = self.module_name
        self.old_file_path = self.file_path
        YamlConfig.save(self)

    @property
    def auto_battle(self) -> str:
        return self.get('auto_battle', '击破站场-强攻速切')

    @auto_battle.setter
    def auto_battle(self, new_value: str):
        self.update('auto_battle', new_value)

    @property
    def resonium_priority(self) -> List[str]:
        return self.get('resonium_priority', [])

    @resonium_priority.setter
    def resonium_priority(self, new_value: List[str]):
        self.update('resonium_priority', new_value)

    @property
    def resonium_priority_str(self) -> str:
        return '\n'.join(self.resonium_priority)

    @property
    def event_priority(self) -> List[str]:
        return self.get('event_priority', [])

    @event_priority.setter
    def event_priority(self, new_value: List[str]):
        self.update('event_priority', new_value)

    @property
    def event_priority_str(self) -> str:
        return '\n'.join(self.event_priority)


def get_all_hollow_zero_challenge_config() -> List[HollowZeroChallengeConfig]:
    config_list: List[HollowZeroChallengeConfig] = []
    dir_path = os_utils.get_path_under_work_dir('config', 'hollow_zero_challenge')
    config_name_list = os.listdir(dir_path)
    for config_name in config_name_list:
        if not config_name.endswith('.yml'):
            continue
        try:
            config = HollowZeroChallengeConfig(config_name[:-4])
            config_list.append(config)
        except Exception:
            log.error('配置文件读取错误 跳过 %s', config_name)
    return config_list


def get_hollow_zero_challenge_new_name() -> str:
    """
    获取新的配置文件的命名
    :return:
    """
    prefix: str = '自定义-'
    max_idx: int = 0
    dir_path = os_utils.get_path_under_work_dir('config', 'hollow_zero_challenge')
    config_name_list = os.listdir(dir_path)
    for config_name in config_name_list:
        if not config_name.endswith('.yml'):
            continue
        if not config_name.startswith(prefix):
            continue
        try:
            idx = int(config_name[len(prefix):-4])
            if idx > max_idx:
                max_idx = idx
        except Exception:
            pass

    return '%s%02d' % (prefix, max_idx)
