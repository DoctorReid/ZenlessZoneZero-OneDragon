from cv2.typing import MatLike
from enum import Enum

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt


class OcrClickResultEnum(Enum):

    OCR_CLICK_SUCCESS: int = 1  # OCR并点击成功
    OCR_CLICK_FAIL: int = 0  # OCR成功但点击失败 基本不会出现
    OCR_CLICK_NOT_FOUND: int = -1  # OCR找不到目标
    AREA_NO_CONFIG: int = -2  # 区域配置找不到


class FindAreaResultEnum(Enum):

    TRUE: int = 1  # 找到了
    FALSE: int = 0  # 找不到
    AREA_NO_CONFIG: int = -2  # 区域配置找不到


def find_area(ctx: OneDragonContext, screen: MatLike, screen_name: str, area_name: str) -> FindAreaResultEnum:
    """
    在一个区域匹配成功后进行点击
    :param ctx: 运行上下文
    :param screen: 屏幕截图
    :param screen_name: 画面名称
    :param area_name: 区域名称
    :return:
    """
    area: ScreenArea = ctx.screen_loader.get_area(screen_name, area_name)
    if area is None:
        return FindAreaResultEnum.AREA_NO_CONFIG

    find: bool = False
    if area.is_text_area:
        rect = area.rect
        part = cv2_utils.crop_image_only(screen, rect)

        ocr_result_map = ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            if str_utils.find_by_lcs(gt(area.text), ocr_result, percent=area.lcs_percent):
                find = True
                break
    elif area.is_template_area:
        rect = area.rect
        part = cv2_utils.crop_image_only(screen, rect)

        mrl = ctx.tm.match_template(part, area.template_sub_dir, area.template_id,
                                    threshold=area.template_match_threshold)
        find = mrl.max is not None

    return FindAreaResultEnum.TRUE if find else FindAreaResultEnum.FALSE


def find_and_click_area(ctx: OneDragonContext, screen: MatLike, screen_name: str, area_name: str) -> OcrClickResultEnum:
    """
    在一个区域匹配成功后进行点击
    :param ctx: 运行上下文
    :param screen: 屏幕截图
    :param screen_name: 画面名称
    :param area_name: 区域名称
    :return:
    """
    area: ScreenArea = ctx.screen_loader.get_area(screen_name, area_name)
    if area is None:
        return OcrClickResultEnum.AREA_NO_CONFIG
    if area.is_text_area:
        rect = area.rect
        part = cv2_utils.crop_image_only(screen, rect)
        # cv2_utils.show_image(part, win_name='debug')

        ocr_result_map = ctx.ocr.run_ocr(part)
        for ocr_result, mrl in ocr_result_map.items():
            if str_utils.find_by_lcs(gt(area.text), ocr_result, percent=area.lcs_percent):
                to_click = mrl.max.center + area.left_top
                if ctx.controller.click(to_click, pc_alt=area.pc_alt):
                    return OcrClickResultEnum.OCR_CLICK_SUCCESS
                else:
                    return OcrClickResultEnum.OCR_CLICK_FAIL

        return OcrClickResultEnum.OCR_CLICK_NOT_FOUND
    elif area.is_template_area:
        rect = area.rect
        part = cv2_utils.crop_image_only(screen, rect)

        mrl = ctx.tm.match_template(part, area.template_sub_dir, area.template_id,
                                    threshold=area.template_match_threshold)
        if mrl.max is None:
            return OcrClickResultEnum.OCR_CLICK_NOT_FOUND
        elif ctx.controller.click(mrl.max.center + rect.left_top, pc_alt=area.pc_alt):
            return OcrClickResultEnum.OCR_CLICK_SUCCESS
        else:
            return OcrClickResultEnum.OCR_CLICK_FAIL
    else:
        return OcrClickResultEnum.OCR_CLICK_FAIL
