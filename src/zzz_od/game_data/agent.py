import os
from enum import Enum
from functools import lru_cache
from typing import Optional, List

from one_dragon.base.yaml_operator import YamlOperator
from one_dragon.utils import os_utils
from one_dragon.utils.i18_utils import gt


class AgentType:

    def __init__(self, cn: str):
        """
        代理人类型
        :param cn:
        """
        self.cn: str = cn


class AgentTypeEnum(Enum):

    SUPPORT = AgentType('支援')
    UNKNOWN = AgentType('未知')

    @classmethod
    def from_name(cls, name):
        if name in AgentTypeEnum.__members__:
            return cls[name]
        else:
            return cls.UNKNOWN


class Agent(YamlOperator):

    def __init__(self, agent_id: str):
        """
        代理人
        """
        YamlOperator.__init__(self, get_agent_yml_path(agent_id))
        self.agent_id: str = agent_id  # 代理人的英文名称
        self.agent_name: str = self.get('agent_name', '')  # 代理人的中文名称
        agent_type_str = self.get('agent_type', '')
        self.agent_type: AgentTypeEnum = AgentTypeEnum.UNKNOWN if agent_type_str not in AgentTypeEnum else AgentTypeEnum[agent_type_str]

    @property
    def agent_type_str(self) -> str:
        return gt(self.agent_type.value.cn)


class AgentLoader:

    def __init__(self):
        self.agent_name_map: dict[str, Agent] = {}
        self.load_all_agents()

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """
        根据中文名称获取
        :param agent_name:
        :return:
        """
        return self.agent_name_map.get(agent_name, None)

    def load_all_agents(self) -> List[Agent]:
        """
        加载所有代理人的信息
        :return:
        """
        agent_list: List[Agent] = []
        root_dir_path = get_agent_root_dir_path()
        agent_files = os.listdir(root_dir_path)
        for agent_file_name in agent_files:
            if not agent_file_name.endswith('yml'):
                continue
            agent = Agent(agent_file_name[:-4])
            agent_list.append(agent)
            self.agent_name_map[agent.agent_name] = agent

        return agent_list


@lru_cache
def get_agent_root_dir_path() -> str:
    """
    代理人配置
    :return:
    """
    return os_utils.get_path_under_work_dir('assets', 'game_data', 'agent')


@lru_cache
def get_agent_yml_path(agent_id: str) -> str:
    """
    获取代理人配置文件路径
    :param agent_id:
    :return:
    """
    return os.path.join(get_agent_root_dir_path(), f'{agent_id}.yml')
