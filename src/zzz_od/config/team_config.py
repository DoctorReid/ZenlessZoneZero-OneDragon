from typing import List

from one_dragon.base.config.yaml_config import YamlConfig


class PredefinedTeamInfo:

    def __init__(self, idx: int, name: str, auto_battle: str):
        self.idx: int = idx  # 在编队数组里的下标
        self.name: str = name  # 编队名称
        self.auto_battle: str = auto_battle  # 对应的自动战斗配置


class TeamConfig(YamlConfig):

    def __init__(self, instance_idx: int):
        YamlConfig.__init__(self, 'team', instance_idx=instance_idx)

    @property
    def team_list(self) -> List[PredefinedTeamInfo]:
        data_list = self.get('team_list', [])

        max_cnt: int = 10
        team_list: List[PredefinedTeamInfo] = []
        for i in range(len(data_list)):
            data = data_list[i]
            team_list.append(PredefinedTeamInfo(i,
                                                name=data.get('name', f'编队{i+1}'),
                                                auto_battle=data.get('auto_battle', '击破站场-强攻速切')))

        current_cnt = len(team_list)
        for i in range(current_cnt + 1, max_cnt + 1):
            team_list.append(PredefinedTeamInfo(i-1, f'编队{i}', '击破站场-强攻速切'))

        return team_list

    def update_team(self, team_info: PredefinedTeamInfo) -> None:
        """
        更新一个配队
        """
        team_list = self.team_list
        if team_info.idx >= len(self.team_list):
            return

        team_list[team_info.idx] = team_info
        data_team_list = [
            {
                'name': team_info.name,
                'auto_battle': team_info.auto_battle
            } for team_info in team_list
        ]

        self.update('team_list', data_team_list)
