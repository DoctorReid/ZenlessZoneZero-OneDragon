import os
import yaml
from typing import List, Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.utils import os_utils
from one_dragon.utils.log_utils import log


class CompendiumMission:

    def __init__(self, mission_name: str, mission_name_display: Optional[str] = None):
        self.mission_name: str = mission_name
        self.mission_name_display: str = mission_name if mission_name_display is None else mission_name_display


class CompendiumMissionType:

    def __init__(self, mission_type_name: str, mission_type_name_display: Optional[str] = None,
                 mission_list: List = None):
        self.mission_type_name: str = mission_type_name
        self.mission_type_name_display: str = mission_type_name
        if mission_type_name_display is not None:
            self.mission_type_name_display = mission_type_name_display
        self.mission_list: List[CompendiumMission] = []
        if mission_list is not None:
            for mission_item in mission_list:
                self.mission_list.append(CompendiumMission(**mission_item))


class CompendiumCategory:

    def __init__(self, category_name: str, mission_type_list: List = None):
        self.category_name: str = category_name
        self.mission_type_list: List[CompendiumMissionType] = []
        if mission_type_list is not None:
            for mission_type_item in mission_type_list:
                self.mission_type_list.append(CompendiumMissionType(**mission_type_item))


class CompendiumTab:

    def __init__(self, tab_name: str, category_list: List = None):
        self.tab_name: str = tab_name
        self.category_list: List[CompendiumCategory] = []
        if category_list is not None:
            for category_list_item in category_list:
                self.category_list.append(CompendiumCategory(**category_list_item))


class CompendiumData:

    def __init__(self, tab_list: List = None):
        self.tab_list: List[CompendiumTab] = []
        if tab_list is not None:
            for tab_item in tab_list:
                self.tab_list.append(CompendiumTab(**tab_item))


class CompendiumService:

    def __init__(self):
        self.data: CompendiumData = CompendiumData()
        self.reload()

    def reload(self) -> None:
        """
        重新加载数据
        :return:
        """
        file_path = os.path.join(
            os_utils.get_path_under_work_dir('assets', 'game_data'),
            'compendium_data.yml'
        )

        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                tab_list: List[dict] = yaml.safe_load(file)
                self.data = CompendiumData(tab_list)
        except Exception:
            log.error(f'文件读取失败 {file_path}', exc_info=True)

    def get_tab_data(self, tab_name: str) -> Optional[CompendiumTab]:
        for tab_item in self.data.tab_list:
            if tab_item.tab_name == tab_name:
                return tab_item
        return None

    def get_category_list_data(self, tab_name: str) -> List[CompendiumCategory]:
        tab = self.get_tab_data(tab_name)

        if tab is None:
            return []

        return tab.category_list

    def get_mission_type_list_data(self, tab_name: str, category_name: str) -> List[CompendiumMissionType]:
        category_list = self.get_category_list_data(tab_name)
        for category_item in category_list:
            if category_item.category_name == category_name:
                return category_item.mission_type_list

        return []

    def get_mission_list_data(self, tab_name: str, category_name: str, mission_type: str) -> List[CompendiumMission]:
        mission_type_list = self.get_mission_type_list_data(tab_name, category_name)
        for mission_type_item in mission_type_list:
            if mission_type_item.mission_type_name == mission_type:
                return mission_type_item.mission_list

        return []

    def get_charge_plan_category_list(self) -> List[ConfigItem]:
        category_config_list: List[ConfigItem] = []

        category_list = self.get_category_list_data('训练')
        for category_item in category_list:
            category_config_list.append(ConfigItem(
                label=category_item.category_name,
                value=category_item.category_name
            ))

        return category_config_list

    def get_charge_plan_mission_type_list(self, category_name: str) -> List[ConfigItem]:
        config_list: List[ConfigItem] = []

        mission_type_list = self.get_mission_type_list_data('训练', category_name)
        for mission_type_item in mission_type_list:
            config_list.append(ConfigItem(
                label=mission_type_item.mission_type_name_display,
                value=mission_type_item.mission_type_name
            ))

        return config_list

    def get_charge_plan_mission_list(self, category_name: str, mission_type: str) -> List[ConfigItem]:
        config_list: List[ConfigItem] = []

        mission_list = self.get_mission_list_data('训练', category_name, mission_type)
        for mission_item in mission_list:
            config_list.append(ConfigItem(
                label=mission_item.mission_name_display,
                value=mission_item.mission_name
            ))

        return config_list

    def get_same_category_mission_type_list(self, mission_type_name: str) -> Optional[List[CompendiumMissionType]]:
        """
        获取与副本相同分类的全部列表
        """
        for tab in self.data.tab_list:
            for category in tab.category_list:
                for mission_type in category.mission_type_list:
                    if mission_type.mission_type_name == mission_type_name:
                        return category.mission_type_list

        return None

    def get_notorious_hunt_plan_mission_type_list(self, category_name: str) -> List[ConfigItem]:
        config_list: List[ConfigItem] = []

        mission_type_list = self.get_mission_type_list_data('挑战', category_name)
        for mission_type_item in mission_type_list:
            config_list.append(ConfigItem(
                label=mission_type_item.mission_type_name_display,
                value=mission_type_item.mission_type_name
            ))

        return config_list