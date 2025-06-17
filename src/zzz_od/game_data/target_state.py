import time
from enum import Enum
from typing import Optional, Dict, Any

class TargetStateCheckWay(Enum):
    """检测方式枚举"""
    ENEMY_TYPE = "enemy_type"  # 敌人类型检测
    STAGGER = "stagger"        # 失衡值检测
    ABNORMAL = "abnormal"      # 异常状态检测
    LOCK_DISTANCE = "lock_distance" # 锁定距离检测

class EnemyTypeValue(Enum):
    """敌人类型-值枚举"""
    NORMAL = 0  # 非强敌
    BOSS = 1    # 强敌
    ELITE = 2   # 精英怪

    @classmethod
    def get_display_map(cls) -> dict:
        return {
            cls.NORMAL: '非强敌',
            cls.BOSS: '强敌',
            cls.ELITE: '精英怪'
        }

class LockDistanceValue(Enum):
    """锁定距离-值枚举"""
    NONE = 0 # 未锁定
    NEAR = 1 # 近距离锁定
    FAR = 2  # 远距离锁定

    @classmethod
    def get_display_map(cls) -> dict:
        return {
            cls.NONE: '未锁定',
            cls.NEAR: '近距离锁定',
            cls.FAR: '远距离锁定'
        }

class AbnormalTypeValue(Enum):
    """七大异常状态-值枚举"""
    ASSAULT = "强击"
    FREEZE = "冻结"
    SHATTER = "碎冰"
    SHOCKED = "感电"
    BURNING = "灼烧"
    CORRUPTION = "侵蚀"
    FROSTBITE = "霜灼"

class TargetStateDef:
    """目标状态定义类 (V5 - 纯数据)"""
    def __init__(self,
                 state_name: str,
                 check_way: TargetStateCheckWay,
                 enabled: bool = True,
                 config_params: Optional[Dict[str, Any]] = None):
        self.state_name = state_name
        self.check_way = check_way
        self.enabled = enabled
        self.config_params = config_params if config_params is not None else {}
