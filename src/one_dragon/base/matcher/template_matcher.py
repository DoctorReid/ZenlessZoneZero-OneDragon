import os
from typing import Optional

import cv2
from cv2.typing import MatLike

from one_dragon.base.matcher.match_result import MatchResultList
from one_dragon.base.screen.template_info import TemplateInfo
from one_dragon.utils import os_utils, cv2_utils
from one_dragon.utils.log_utils import log


class TemplateMatcher:

    def __init__(self):
        self.template: dict[str, TemplateInfo] = {}

    def load_template(self, template_id: str, sub_dir: Optional[str] = None) -> Optional[TemplateInfo]:
        """
        加载某个模板到内存
        :param template_id: 模板id
        :param sub_dir: 子文件夹
        :return: 模板图片
        """
        dir_path = os.path.join(os_utils.get_path_under_work_dir('assets', 'template', sub_dir), template_id)
        if not os.path.exists(dir_path):  # 注意上方不要直接用get_path_under_work_dir获取全路径 避免创建空文件夹
            return None
        template: TemplateInfo = TemplateInfo()
        template.origin = cv2_utils.read_image(os.path.join(dir_path, 'origin.png'))
        template.gray = cv2_utils.read_image(os.path.join(dir_path, 'gray.png'))
        template.mask = cv2_utils.read_image(os.path.join(dir_path, 'mask.png'))

        feature_path = os.path.join(dir_path, 'features.xml')
        if os.path.exists(feature_path):
            file_storage = cv2.FileStorage(feature_path, cv2.FILE_STORAGE_READ)
            # 读取特征点和描述符
            template.kps = cv2_utils.feature_keypoints_from_np(file_storage.getNode("keypoints").mat())
            template.desc = file_storage.getNode("descriptors").mat()
            # 释放文件存储对象
            file_storage.release()
        else:
            if template.origin is not None and template.mask is not None:
                template.kps, template.desc = cv2_utils.feature_detect_and_compute(template.origin, template.mask)

        key = '%s:%s' % ('' if sub_dir is None else sub_dir, template_id)
        self.template[key] = template
        return template

    def pop_template(self, template_id: str):
        """
        将某个模板从内存中删除
        :param template_id: 模板id
        :return:
        """
        if template_id in self.template:
            del self.template[template_id]

    def get_template(self, template_id: str, sub_dir: Optional[str] = None) -> TemplateInfo:
        """
        获取某个模板
        :param template_id: 模板id
        :param sub_dir: 子文件夹
        :return: 模板图片
        """
        key = '%s:%s' % ('' if sub_dir is None else sub_dir, template_id)
        if key in self.template:
            return self.template[key]
        else:
            return self.load_template(template_id, sub_dir)

    def match_template(self, source: MatLike, template_id: str,
                       template_sub_dir: Optional[str] = None,
                       template_type: str = 'origin',
                       threshold: float = 0.5,
                       mask: MatLike = None,
                       ignore_template_mask: bool = False,
                       only_best: bool = True,
                       ignore_inf: bool = True) -> MatchResultList:
        """
        在原图中 匹配模板 如果模板图中有掩码图 会自动使用
        :param source: 原图
        :param template_id: 模板id
        :param template_sub_dir: 模板的子文件夹
        :param template_type: 模板类型
        :param threshold: 匹配阈值
        :param mask: 额外使用的掩码 与原模板掩码叠加
        :param ignore_template_mask: 是否忽略模板自身的掩码
        :param only_best: 只返回最好的结果
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        template: TemplateInfo = self.get_template(template_id, template_sub_dir)
        if template is None:
            log.error('未加载模板 %s' % template_id)
            return MatchResultList()

        mask_usage = None
        if not ignore_template_mask:
            mask_usage = cv2.bitwise_or(mask_usage, template.mask) if mask_usage is not None else template.mask
        if mask is not None:
            mask_usage = cv2.bitwise_or(mask_usage, mask) if mask_usage is not None else mask
        return cv2_utils.match_template(source, template.get(template_type), threshold, mask=mask_usage,
                                        only_best=only_best, ignore_inf=ignore_inf)
