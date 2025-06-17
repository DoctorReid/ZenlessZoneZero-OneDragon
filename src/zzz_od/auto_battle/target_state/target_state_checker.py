import re
from typing import List, Tuple, Any

from cv2.typing import MatLike

from one_dragon.base.cv_process.cv_pipeline import CvPipelineContext
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.target_state import AbnormalTypeValue


class TargetStateChecker:
    """
    一个高效、职责单一的目标状态检测器。
    它提供高级接口，一次调用即可返回多个相关的状态结果，内部封装了对CV流水线的调用。
    """

    _ABNORMAL_KEYWORDS = {
        "霜": AbnormalTypeValue.FROSTBITE.value,
        "侵": AbnormalTypeValue.CORRUPTION.value, "蚀": AbnormalTypeValue.CORRUPTION.value,
        "烧": AbnormalTypeValue.BURNING.value,
        "感": AbnormalTypeValue.SHOCKED.value, "电": AbnormalTypeValue.SHOCKED.value,
        "碎": AbnormalTypeValue.SHATTER.value, "冰": AbnormalTypeValue.SHATTER.value,
        "冻": AbnormalTypeValue.FREEZE.value, "结": AbnormalTypeValue.FREEZE.value,
        "强": AbnormalTypeValue.ASSAULT.value, "击": AbnormalTypeValue.ASSAULT.value,
    }
    """异常状态关键字与标准名称的宽松匹配映射"""

    def __init__(self, ctx: ZContext):
        """
        初始化检测器
        :param ctx: 全局上下文
        """
        self.ctx: ZContext = ctx

    def _run_pipeline(self, pipeline_name: str, screen: MatLike) -> CvPipelineContext | None:
        """
        运行指定的CV流水线
        :param pipeline_name: 流水线名称
        :param screen: 屏幕截图
        :return: 流水线执行上下文，失败则返回None
        """
        # 在自动战斗的上下文中，强制关闭调试模式以保证性能
        return self.ctx.cv_service.run_pipeline(pipeline_name, screen, debug_mode=False)

    def check_lock_on(self, screen: MatLike) -> List[Tuple[str, Any]]:
        """
        检测目标锁定状态。统一使用 lock-far 进行检测。
        :param screen: 屏幕截图
        :return: 状态元组列表。
                 - [('目标-近距离锁定', True)]
                 - [('目标-未锁定', True)]
        """
        result = self._run_pipeline('lock-far', screen)
        if result is not None and result.is_success and len(result.contours) > 0:
            # 根据用户要求，使用宽松的 far 检测，但统一返回近距离锁定的状态
            return [('目标-近距离锁定', True)]
        else:
            return [('目标-未锁定', True)]

    def check_enemy_type_and_stagger(self, screen: MatLike) -> List[Tuple[str, Any]]:
        """
        检测敌人类型（是否为Boss）并获取其失衡值。
        :param screen: 屏幕截图
        :return: 状态元组列表。
                 - 如果是Boss, 返回 [('目标-强敌', True), ('目标-失衡值', 75)]
                 - 如果是普通敌人, 返回 [('目标-非强敌', True)]
        """
        result = self._run_pipeline('boss_stun', screen)
        if result is None or not result.is_success or result.ocr_result is None:
            return [('目标-非强敌', True)]

        # 根据返回结果的类型，用不同的方式获取文本
        ocr_result_obj = result.ocr_result
        if isinstance(ocr_result_obj, dict):
            # 如果是字典，将其所有的键拼接成一个文本字符串
            ocr_text = "".join(ocr_result_obj.keys())
        else:
            # 否则，假定它有get_text方法
            ocr_text = ocr_result_obj.get_text()

        if not ocr_text:
            return [('目标-非强敌', True)]
            
        match = re.search(r'\d+', ocr_text)

        if match:
            stagger_value = int(match.group(0))
            return [('目标-强敌', True), ('目标-失衡值', stagger_value)]
        else:
            return [('目标-非强敌', True)]

    def check_abnormal_statuses(self, screen: MatLike) -> List[Tuple[str, Any]]:
        """
        检测目标所有的异常状态。
        :param screen: 屏幕截图
        :return: 状态元组列表，例如 [('目标-异常-强击', True), ('目标-异常-燃烧', True)]
        """
        result = self._run_pipeline('ocr-abnormal', screen)
        if result is None or not result.is_success or result.ocr_result is None:
            return []

        # 根据返回结果的类型，用不同的方式获取文本
        ocr_result_obj = result.ocr_result
        if isinstance(ocr_result_obj, dict):
            # 如果是字典，将其所有的键拼接成一个文本字符串
            ocr_text = "".join(ocr_result_obj.keys())
        else:
            # 否则，假定它有get_text方法
            ocr_text = ocr_result_obj.get_text()

        if not ocr_text:
            return []
            
        detected_statuses = set()
        for char, standard_name in self._ABNORMAL_KEYWORDS.items():
            if char in ocr_text:
                detected_statuses.add(standard_name)

        return [(f'目标-异常-{status}', True) for status in detected_statuses]