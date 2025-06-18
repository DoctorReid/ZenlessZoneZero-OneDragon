import re
from typing import List, Tuple, Any

from cv2.typing import MatLike

from one_dragon.base.cv_process.cv_pipeline import CvPipelineContext
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.target_state import DetectionTask, TargetStateDef, TargetCheckWay


class TargetStateChecker:
    """
    一个完全由数据驱动的通用目标状态检测器
    """

    def __init__(self, ctx: ZContext):
        """
        初始化检测器
        :param ctx: 全局上下文
        """
        self.ctx: ZContext = ctx
        self._check_way_handlers = {
            TargetCheckWay.CONTOUR_COUNT_IN_RANGE: self._check_contour_count,
            TargetCheckWay.OCR_RESULT_AS_NUMBER: self._check_ocr_as_number,
            TargetCheckWay.OCR_TEXT_CONTAINS: self._check_ocr_text_contains,
            TargetCheckWay.DIRECT_RETURN: self._check_direct_return,
        }

    def run_task(self, screen: MatLike, task: DetectionTask, debug_mode: bool = False) -> Tuple[CvPipelineContext, List[Tuple[str, Any]]]:
        """
        运行一个检测任务组，并返回所有解读出的状态
        :param screen: 屏幕截图
        :param task: 检测任务组的定义
        :param debug_mode: 是否开启CV流水线的调试模式
        :return: CV结果上下文, 状态元组列表 (state_name, result)
        """
        # 1. 运行一次CV流水线
        cv_result = self.ctx.cv_service.run_pipeline(task.pipeline_name, screen, debug_mode=debug_mode)

        # 2. 循环解读结果
        results = []
        for state_def in task.state_definitions:
            interpreted_value = self._interpret_result(cv_result, state_def)
            results.append((state_def.state_name, interpreted_value))

        return cv_result, results

    def _interpret_result(self, cv_result: CvPipelineContext, state_def: TargetStateDef) -> Any:
        """
        根据单个状态定义，解读一份CV结果。
        现在返回True, (True, value), False, 或 None
        """
        if cv_result is None or not cv_result.is_success:
            # CV失败时，视为未检测到
            return None if state_def.clear_on_miss else False

        handler = self._check_way_handlers.get(state_def.check_way)
        if handler:
            return handler(cv_result, state_def)
        else:
            log.warn(f"未知的 TargetCheckWay: {state_def.check_way} for state {state_def.state_name}")
            return False # 未知check_way视为不处理

    def _check_contour_count(self, cv_result: CvPipelineContext, state_def: TargetStateDef) -> bool | None:
        """
        处理 CONTOUR_COUNT_IN_RANGE
        """
        params = state_def.check_params
        count = len(cv_result.contours)
        min_count = params.get('min_count', 0)
        max_count = params.get('max_count', 999)
        if min_count <= count <= max_count:
            return True
        else:
            return None if state_def.clear_on_miss else False

    def _check_ocr_as_number(self, cv_result: CvPipelineContext, state_def: TargetStateDef) -> tuple | bool | None:
        """
        处理 OCR_RESULT_AS_NUMBER
        """
        try:
            # 兼容dict和OcrResult两种返回类型
            ocr_text = "".join(cv_result.ocr_result.keys()) if isinstance(cv_result.ocr_result,
                                                                          dict) else cv_result.ocr_result.get_text()
            match = re.search(r'\d+', ocr_text)
            if match:
                return True, int(match.group(0))
        except (ValueError, TypeError, AttributeError):
            pass  # 异常情况视为未识别到

        # 对于OCR_RESULT_AS_NUMBER，如果没有数字，则根据clear_on_miss决定
        return None if state_def.clear_on_miss else False

    def _check_ocr_text_contains(self, cv_result: CvPipelineContext, state_def: TargetStateDef) -> bool | None:
        """
        处理 OCR_TEXT_CONTAINS
        """
        params = state_def.check_params
        try:
            # 兼容dict和OcrResult两种返回类型
            ocr_text = "".join(cv_result.ocr_result.keys()) if isinstance(cv_result.ocr_result,
                                                                          dict) else cv_result.ocr_result.get_text()
            if not ocr_text: # 初始的空文本检查
                return None if state_def.clear_on_miss else False

            contains = params.get('contains', [])
            if isinstance(contains, str):
                contains = [contains]

            mode = params.get('mode', 'any')
            case_sensitive = params.get('case_sensitive', False)
            exclude = params.get('exclude', [])
            if isinstance(exclude, str):
                exclude = [exclude]

            # 处理大小写
            processed_ocr_text = ocr_text
            if not case_sensitive:
                processed_ocr_text = ocr_text.lower()
                processed_contains = [c.lower() for c in contains]
                processed_exclude = [e.lower() for e in exclude]
            else:
                processed_contains = contains
                processed_exclude = exclude

            # 检查排除项
            for ex_text in processed_exclude:
                if ex_text in processed_ocr_text:
                    return None if state_def.clear_on_miss else False

            # 检查包含项
            if mode == 'any':
                if any(c_text in processed_ocr_text for c_text in processed_contains):
                    return True
            elif mode == 'all':
                if all(c_text in processed_ocr_text for c_text in processed_contains):
                    return True
            
            # 如果以上条件都不满足，则说明未命中
            return None if state_def.clear_on_miss else False

        except (ValueError, TypeError, AttributeError):
            # 异常情况也视为无有效结果
            return None if state_def.clear_on_miss else False

    # def _check_direct_return(self, cv_result: CvPipelineContext, state_def: TargetStateDef) -> Any:
    #     """
    #     处理 DIRECT_RETURN，直接返回在check_params中指定的结果
    #     CV结果在此方法中通常不被使用，但保持参数一致性
    #     """
    #     params = state_def.check_params
    #     value_to_return = params.get('value_to_return')

    #     # 检查是否返回一个带值的元组
    #     if isinstance(value_to_return, tuple) and len(value_to_return) == 2 and value_to_return[0] is True:
    #         return value_to_return # 返回 (True, value)

    #     # 检查是否返回布尔值
    #     if isinstance(value_to_return, bool):
    #         if value_to_return:
    #             return True
    #         else: # value_to_return is False
    #             return None if state_def.clear_on_miss else False

    #     # 如果 value_to_return 未提供或是无效类型，则视为未命中
    #     return None if state_def.clear_on_miss else False