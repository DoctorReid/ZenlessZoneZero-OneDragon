from typing import Optional, List

from cv2.typing import MatLike

from one_dragon.base.cv_process.cv_pipeline import CvPipelineContext
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.target_state import EnemyTypeValue, LockDistanceValue, TargetStateDef, TargetStateCheckWay


def _run_pipeline_and_check_success(ctx: ZContext, screen: MatLike, config_params: dict) -> CvPipelineContext | None:
    """
    运行指定的CV流水线，并返回一个标记成功与否的布尔值
    :return: 成功则为True，否则为False
    """
    pipeline_name = config_params.get('pipeline_name')
    if not pipeline_name:
        return None

    # V15 增加debug参数
    debug = ctx.env_config.is_debug and config_params.get('debug', False)
    return ctx.cv_service.run_pipeline(pipeline_name, screen, debug_mode=debug)


def check_enemy_type(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测敌人类型（普通/强敌）
    """
    result = _run_pipeline_and_check_success(ctx, screen, config_params)
    if result is None:
        return None

    if result.is_success:
        return EnemyTypeValue.ELITE.value
    else:
        return EnemyTypeValue.NORMAL.value


def check_stagger_value(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测目标的失衡值
    """
    result = _run_pipeline_and_check_success(ctx, screen, config_params)
    if result is None:
        return None

    if result.is_success:
        # 假设流水线成功后，结果存储在 ocr_result 中
        try:
            return int(result.ocr_result.get_text())
        except (ValueError, AttributeError):
            return None
    else:
        return None


def check_abnormal_status(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测目标身上指定的单个异常状态
    """
    result = _run_pipeline_and_check_success(ctx, screen, config_params)
    if result is None:
        return None

    return 1 if result.is_success else None


def check_lock_distance(ctx: ZContext, screen: MatLike, config_params: dict) -> Optional[int]:
    """
    检测锁定距离
    """
    result = _run_pipeline_and_check_success(ctx, screen, config_params)
    if result is None:
        return None

    # TODO: 根据不同的流水线结果，判断是近还是远
    return LockDistanceValue.NEAR.value if result.is_success else LockDistanceValue.NONE.value


# 内置目标状态定义
BUILTIN_TARGET_STATE_DEFS: List[TargetStateDef] = [
    # 敌人类型检测 - 使用 `enemy_type_elite` 流水线
    TargetStateDef("敌人类型",
                   TargetStateCheckWay.ENEMY_TYPE,
                   {'pipeline_name': 'enemy_type_elite', 'debug': True}),

    # 失衡值检测 - 使用 `enemy_stagger` 流水线
    TargetStateDef("目标-失衡值",
                   TargetStateCheckWay.STAGGER,
                   {'pipeline_name': 'enemy_stagger', 'debug': True}),

    # 锁定距离检测 - 使用 `lock_distance_near` 流水线
    TargetStateDef("目标-锁定状态",
                   TargetStateCheckWay.LOCK_DISTANCE,
                   {'pipeline_name': 'lock_distance_near', 'debug': True}),

    # 异常状态检测 (每个状态独立定义)
    TargetStateDef("目标-异常-强击", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_qiangji"}),
    TargetStateDef("目标-异常-冻结", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_dongjie"}),
    TargetStateDef("目标-异常-碎冰", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_suibing"}),
    TargetStateDef("目标-异常-感电", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_gandian"}),
    TargetStateDef("目标-异常-燃烧", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_ranshao"}),
    TargetStateDef("目标-异常-侵蚀", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_qinshi"}),
    TargetStateDef("目标-异常-霜寒", TargetStateCheckWay.ABNORMAL, {"pipeline_name": "abnormal_shuanghan"}),
]