from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


class TargetCheckWay(Enum):
    """
    定义如何解读CV流水线返回的结果
    """
    CONTOUR_COUNT_IN_RANGE = 'contour_count_in_range'
    CONNECTED_AREA_WIDTH_RATIO = 'connected_area_width_ratio'
    CONNECTED_AREA_LENGTH_RATIO = 'connected_area_length_ratio'
    TEMPLATE_MATCH_CONFIDENCE = 'template_match_confidence'
    OCR_RESULT_AS_NUMBER = 'ocr_result_as_number'
    OCR_TEXT_CONTAINS = 'ocr_text_contains'
    DIRECT_RETURN = 'direct_return'  # 新增：直接返回指定结果，用于测试


@dataclass
class TargetStateDef:
    """
    状态解读器：定义如何从一份CV结果中提取一个具体的状态。
    """
    state_name: str
    check_way: TargetCheckWay
    check_params: Dict[str, Any] = field(default_factory=dict)
    # 当状态未命中时，是否发送False来清除状态
    clear_on_miss: bool = True


@dataclass
class DetectionTask:
    """
    检测任务组：定义一次完整的、可调度的检测活动。
    """
    task_id: str
    pipeline_name: str
    state_definitions: List[TargetStateDef]
    interval: float = 1.0
    is_async: bool = False
    # 用于动态频率的特殊配置
    dynamic_interval_config: dict = field(default_factory=dict)


# 状态检测任务注册表
# 这是未来扩展的唯一修改点
DETECTION_TASKS: List[DetectionTask] = [
    # 任务1: 锁定检测
    DetectionTask(
        task_id='lock_on',
        pipeline_name='lock-far',
        interval=0.1,
        dynamic_interval_config={
            'state_to_watch': '目标-近距离锁定',
            'interval_if_state': 1.0,  # 锁定时用1秒间隔
            'interval_if_not_state': 0.1,  # 未锁定时用0.1秒间隔
            'kwarg_if_state': 'check_lock_interval_locked',
            'kwarg_if_not_state': 'check_lock_interval_unlocked'
        },
        state_definitions=[
            TargetStateDef('目标-近距离锁定', TargetCheckWay.CONTOUR_COUNT_IN_RANGE, {'min_count': 2}),
        ]
    ),

    # 任务2: 异常状态检测 (一次OCR，多次解读)
    DetectionTask(
        task_id='abnormal_statuses',
        pipeline_name='ocr-abnormal',
        interval=1.0,
        is_async=True,
        state_definitions=[
            TargetStateDef('目标-异常-灼烧', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['烧'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-冻结', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['冻', '结'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-霜灼', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['霜'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-感电', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['感', '电'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-碎冰', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['碎', '冰'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-侵蚀', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['侵', '蚀'], 'mode': 'any'}, clear_on_miss=False),
            TargetStateDef('目标-异常-强击', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': ['强', '击'], 'mode': 'any'}, clear_on_miss=False),
        ]
    ),

    # 任务3: Boss状态检测 (一次OCR，混合解读)
    DetectionTask(
        task_id='boss_status',
        pipeline_name='boss_stun',
        interval=0.5,
        is_async=True,
        state_definitions=[
            TargetStateDef('目标-失衡值', TargetCheckWay.OCR_RESULT_AS_NUMBER),
            TargetStateDef('目标-强敌', TargetCheckWay.OCR_TEXT_CONTAINS, {'contains': '强敌'}),
        ]
    ),

    # 任务4: 全面测试用任务 (DIRECT_RETURN)
    DetectionTask(
        task_id='test_direct_return_comprehensive',
        pipeline_name='lock-far',  # 使用一个已知存在的流水线
        interval=1.0,  # 测试任务通常不需要太频繁
        is_async=False, # 同步执行便于观察
        state_definitions=[
            # 测试1: 直接返回True
            TargetStateDef(
                '测试状态-直接True',
                TargetCheckWay.DIRECT_RETURN,
                {'value_to_return': True}
                # clear_on_miss 默认为 True，但在这里不生效，因为是返回True
            ),
            # 测试2: 直接返回False，并且 clear_on_miss 为 True (默认行为)
            TargetStateDef(
                '测试状态-直接False清除',
                TargetCheckWay.DIRECT_RETURN,
                {'value_to_return': False}
                # clear_on_miss 默认为 True
            ),
            # 测试3: 直接返回False，并且 clear_on_miss 为 False
            TargetStateDef(
                '测试状态-直接False不清除',
                TargetCheckWay.DIRECT_RETURN,
                {'value_to_return': False},
                clear_on_miss=False
            ),
            # 测试4: check_params中未提供 value_to_return (预期返回None)
            TargetStateDef(
                '测试状态-直接返回无参数',
                TargetCheckWay.DIRECT_RETURN
                # check_params 为空, clear_on_miss 默认为 True
            ),
            # 测试5: value_to_return 不是布尔值 (预期返回None)
            TargetStateDef(
                '测试状态-直接返回无效值',
                TargetCheckWay.DIRECT_RETURN,
                {'value_to_return': 'not_a_boolean'}
            ),
        ]
    )
]
