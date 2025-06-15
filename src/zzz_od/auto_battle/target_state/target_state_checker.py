from typing import Optional, List, Dict, Any

from cv2.typing import MatLike

from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.target_state import EnemyTypeValue, LockDistanceValue, TargetStateDef, TargetStateCheckWay


def check_enemy_type(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测敌人类型（普通/强敌）
    Args:
        screen: 当前屏幕截图
        config_params: 配置参数
    Returns:
        1 (强敌) 或 0 (非强敌)。若未检测到则返回 None (V12)
    """
    # TODO: 实现实际的图像分析逻辑
    # V12: 使用 mock_value 参数进行模拟输出，若未设置则返回 None
    return config_params.get('mock_value')


def check_stagger_value(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测目标的失衡值
    Args:
        screen: 当前屏幕截图
        config_params: 配置参数
    Returns:
        0-100之间的整数值。若未检测到则返回 None (V12)
    """
    # TODO: 实现实际的图像分析逻辑
    # V12: 使用 mock_value 参数进行模拟输出，若未设置则返回 None
    return config_params.get('mock_value')


def check_abnormal_status(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测目标身上指定的单个异常状态
    Args:
        screen: 当前屏幕截图
        config_params: 配置参数, 需包含'abnormal_name'键
    Returns:
        1 (存在)。若未检测到则返回 None (V12)
    """
    abnormal_name: Optional[str] = config_params.get('abnormal_name')
    if not abnormal_name:
        return None

    # TODO: 实现实际的图像分析逻辑 - 这里只检测指定的异常状态
    # V12: 使用 mock_value 参数进行模拟输出，若未设置则返回 None
    return config_params.get('mock_value')


def check_lock_distance(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测锁定距离
    Args:
        screen: 当前屏幕截图
        config_params: 配置参数
    Returns:
        0 (无), 1 (近), 2 (远)。若未检测到则返回 None (V12)
    """
    # TODO: 实现实际的图像分析逻辑
    # V12: 使用 mock_value 参数进行模拟输出，若未设置则返回 None
    return config_params.get('mock_value')

# V6 - 内置目标状态定义 (增加mock_value方便调试)
# --- 第二轮测试场景 ---
BUILTIN_TARGET_STATE_DEFS: List[TargetStateDef] = [
    # 敌人类型检测 - 模拟一个“非强敌”
    TargetStateDef("敌人类型", TargetStateCheckWay.ENEMY_TYPE,
                   config_params={'mock_value': EnemyTypeValue.NORMAL.value}),

    # 失衡值检测 - 模拟一个“25”
    TargetStateDef("目标-失衡值", TargetStateCheckWay.STAGGER,
                   config_params={'mock_value': 25}),

    # 锁定距离检测 - 模拟一个“近距离”
    TargetStateDef("目标-锁定状态", TargetStateCheckWay.LOCK_DISTANCE,
                   config_params={'mock_value': LockDistanceValue.NEAR.value}),

    # 异常状态检测 (每个状态独立定义)
    TargetStateDef("目标-异常-强击", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "强击"}),
    TargetStateDef("目标-异常-冻结", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "冻结"}),
    TargetStateDef("目标-异常-碎冰", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "碎冰"}),
    TargetStateDef("目标-异常-感电", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "感电", "mock_value": 1}),
    TargetStateDef("目标-异常-燃烧", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "燃烧"}),
    TargetStateDef("目标-异常-侵蚀", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "侵蚀", "mock_value": 1}),
    TargetStateDef("目标-异常-霜寒", TargetStateCheckWay.ABNORMAL,
                   config_params={"abnormal_name": "霜寒"}),
]