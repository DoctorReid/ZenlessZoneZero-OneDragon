import cv2
from cv2.typing import MatLike
from typing import Optional

from one_dragon.base.matcher.match_result import MatchResultList
from one_dragon.base.screen.template_info import TemplateInfo
from one_dragon.base.screen.template_loader import TemplateLoader
from one_dragon.utils import cv2_utils
from one_dragon.utils.log_utils import log


class TemplateMatcher:

    def __init__(self, template_loader: TemplateLoader):
        self.template_loader: TemplateLoader = template_loader

    def match_template(self, source: MatLike,
                       template_sub_dir: str,
                       template_id: str,
                       template_type: str = 'raw',
                       threshold: float = 0.5,
                       mask: MatLike = None,
                       ignore_template_mask: bool = False,
                       only_best: bool = True,
                       ignore_inf: bool = True) -> MatchResultList:
        """
        在原图中 匹配模板 如果模板图中有掩码图 会自动使用
        :param source: 原图
        :param template_sub_dir: 模板的子文件夹
        :param template_id: 模板id
        :param template_type: 模板类型
        :param threshold: 匹配阈值
        :param mask: 额外使用的掩码 与原模板掩码叠加
        :param ignore_template_mask: 是否忽略模板自身的掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        template: TemplateInfo = self.template_loader.get_template(template_sub_dir, template_id)
        if template is None:
            log.error('未加载模板 %s' % template_id)
            return MatchResultList()

        mask_usage: Optional[MatLike] = None
        if not ignore_template_mask:
            mask_usage = cv2.bitwise_or(mask_usage, template.mask) if mask_usage is not None else template.mask
        if mask is not None:
            mask_usage = cv2.bitwise_or(mask_usage, mask) if mask_usage is not None else mask
        return cv2_utils.match_template(source, template.get_image(template_type), threshold, mask=mask_usage,
                                        only_best=only_best, ignore_inf=ignore_inf)
