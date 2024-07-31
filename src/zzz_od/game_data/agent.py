from enum import Enum

from one_dragon.utils.i18_utils import gt


class AgentTypeEnum(Enum):

    ATTACK = '强攻'
    STUN = '击破'
    SUPPORT = '支援'
    DEFENSE = '防护'
    ANOMALY = '异常'
    UNKNOWN = '未知'

    @classmethod
    def from_name(cls, name):
        if name in AgentTypeEnum.__members__:
            return cls[name]
        else:
            return cls.UNKNOWN


class DmgTypeEnum(Enum):

    ELECTRIC = '电属性'
    ETHER = '以太'
    PHYSICAL = '物理'
    FIRE = '火属性'
    ICE = '冰属性'
    UNKNOWN = '未知'

    @classmethod
    def from_name(cls, name):
        if name in DmgTypeEnum.__members__:
            return cls[name]
        else:
            return cls.UNKNOWN


class RareTypeEnum(Enum):

    S = 'S'
    A = 'A'
    UNKNOWN = '未知'

    @classmethod
    def from_name(cls, name):
        if name in RareTypeEnum.__members__:
            return cls[name]
        else:
            return cls.UNKNOWN


class Agent:

    def __init__(self, agent_id: str, agent_name: str,
                 rare_type: RareTypeEnum,
                 agent_type: AgentTypeEnum,
                 dmg_type: DmgTypeEnum):
        """
        代理人
        """
        self.agent_id: str = agent_id  # 代理人的英文名称
        self.agent_name: str = agent_name  # 代理人的中文名称
        self.rare_type: RareTypeEnum = rare_type  # 稀有等级

        self.agent_type: AgentTypeEnum = agent_type  # 角色类型
        self.dmg_type: DmgTypeEnum = dmg_type  # 伤害类型

    @property
    def agent_type_str(self) -> str:
        return gt(self.agent_type.value)


class AgentEnum(Enum):

    ANBY = Agent('anby', '安比', RareTypeEnum.A, AgentTypeEnum.STUN, DmgTypeEnum.ELECTRIC)
    ANTON = Agent('anton', '安东', RareTypeEnum.A, AgentTypeEnum.ATTACK, DmgTypeEnum.ELECTRIC)
    BEN = Agent('ben', '本', RareTypeEnum.A, AgentTypeEnum.DEFENSE, DmgTypeEnum.FIRE)
    BILLY = Agent('billy', '比利', RareTypeEnum.A, AgentTypeEnum.ATTACK, DmgTypeEnum.ELECTRIC)
    CORIN = Agent('corin', '可琳', RareTypeEnum.A, AgentTypeEnum.ATTACK, DmgTypeEnum.PHYSICAL)
    ELLEN = Agent('ellen', '艾莲', RareTypeEnum.S, AgentTypeEnum.ATTACK, DmgTypeEnum.ICE)
    GRACE = Agent('grace', '格莉丝', RareTypeEnum.S, AgentTypeEnum.ANOMALY, DmgTypeEnum.ELECTRIC)
    KOLEDA = Agent('koleda', '珂蕾妲', RareTypeEnum.S, AgentTypeEnum.STUN, DmgTypeEnum.FIRE)
    LUCY = Agent('lucy', '露西', RareTypeEnum.A, AgentTypeEnum.SUPPORT, DmgTypeEnum.FIRE)
    LYCAON = Agent('lycaon', '莱卡恩', RareTypeEnum.S, AgentTypeEnum.STUN, DmgTypeEnum.ICE)
    NEKOMATA = Agent('nekomata', '猫又', RareTypeEnum.S, AgentTypeEnum.ATTACK, DmgTypeEnum.PHYSICAL)
    NICOLE = Agent('nicole', '妮可', RareTypeEnum.A, AgentTypeEnum.SUPPORT, DmgTypeEnum.ETHER)
    PIPER = Agent('piper', '派派', RareTypeEnum.A, AgentTypeEnum.ANOMALY, DmgTypeEnum.PHYSICAL)
    RINA = Agent('rina', '丽娜', RareTypeEnum.S, AgentTypeEnum.SUPPORT, DmgTypeEnum.ELECTRIC)
    SOLDIER_11 = Agent('soldier_11', '11号', RareTypeEnum.S, AgentTypeEnum.ATTACK, DmgTypeEnum.FIRE)
    SOUKAKU = Agent('soukaku', '苍角', RareTypeEnum.A, AgentTypeEnum.SUPPORT, DmgTypeEnum.ICE)
    ZHU_YUAN = Agent('zhu_yuan', '朱鸢', RareTypeEnum.S, AgentTypeEnum.ATTACK, DmgTypeEnum.ETHER)
