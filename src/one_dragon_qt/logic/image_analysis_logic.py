# coding: utf-8
import os
from typing import List, Dict, Type

import cv2
import numpy as np

from one_dragon.base.cv_process.cv_pipeline import CvPipeline, CvPipelineContext
from one_dragon.base.cv_process.cv_step import CvStep
from one_dragon.base.screen.template_info import TemplateInfo
from one_dragon.utils import cv2_utils
from zzz_od.context.zzz_context import ZContext
from one_dragon.base.cv_process.cv_code_generator import CvCodeGenerator


class ImageAnalysisLogic:
    """
    CV流水线可视化调试器的UI逻辑层 (前台)
    负责响应界面事件，调用核心CV服务，并管理界面状态
    """

    def __init__(self, ctx: ZContext):
        """
        业务逻辑的初始化
        """
        self.ctx: ZContext = ctx
        self.cv_service = ctx.cv_service  # 从上下文中获取核心服务

        self.pipeline: CvPipeline = CvPipeline()
        self.context: CvPipelineContext = None
        self.active_pipeline_name: str = None  # 当前激活的流水线名称

        self.view_options: List[str] = ['原始图像', '遮罩', '最终结果']
        self.current_view_index: int = 0

        # UI层仍然需要知道有哪些可用的步骤，以便在界面上显示
        self.available_steps: Dict[str, Type[CvStep]] = self.cv_service.available_steps

    def get_available_step_names(self) -> List[str]:
        """
        获取所有可用步骤的名称
        """
        return list(self.available_steps.keys())

    def add_step(self, step_name: str):
        """
        往流水线中添加一个步骤
        """
        if step_name in self.available_steps:
            step_class = self.available_steps[step_name]
            self.pipeline.steps.append(step_class())

    def remove_step(self, index: int):
        """
        从流水线中删除一个步骤
        """
        if 0 <= index < len(self.pipeline.steps):
            self.pipeline.steps.pop(index)

    def move_step_up(self, index: int):
        """
        上移一个步骤
        """
        if index > 0 and index < len(self.pipeline.steps):
            self.pipeline.steps.insert(index - 1, self.pipeline.steps.pop(index))

    def move_step_down(self, index: int):
        """
        下移一个步骤
        """
        if index >= 0 and index < len(self.pipeline.steps) - 1:
            self.pipeline.steps.insert(index + 1, self.pipeline.steps.pop(index))

    def execute_pipeline(self) -> tuple[np.ndarray, List[str]]:
        """
        执行流水线
        """
        if self.context is None or self.context.source_image is None:
            return None, ["请先加载图片"]

        # 直接调用 pipeline 的 execute，并传入 service
        self.context = self.pipeline.execute(
            source_image=self.context.source_image,
            service=self.cv_service,
            debug_mode=True
        )

        # 执行后默认显示最终结果
        self.current_view_index = 2
        return self.get_display_image(), self.context.analysis_results

    def toggle_display(self):
        """
        切换显示的图像
        """
        self.current_view_index = (self.current_view_index + 1) % len(self.view_options)

    def get_current_view_name(self) -> str:
        """
        获取当前视图的名称
        """
        if not self.view_options:
            return "无"
        return self.view_options[self.current_view_index]

    def load_image(self, file_path: str) -> bool:
        """
        从文件路径加载图片，并初始化相关状态
        """
        try:
            # 直接使用cv2.imread确保读取的是BGR格式
            image_bgr = cv2.imread(file_path)
            if image_bgr is None:
                return False

            # 立刻转换为RGB格式，确保后续所有操作的颜色空间正确
            source_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            self.context = CvPipelineContext(source_image, service=self.cv_service, debug_mode=True)

            height, width, _ = source_image.shape
            self.context.mask_image = np.full((height, width), 255, dtype=np.uint8)

            self.current_view_index = 0
            return True
        except Exception:
            return False

    def get_display_image(self) -> np.ndarray:
        """
        获取当前用于显示的图像
        """
        if self.context is None:
            return None

        view_name = self.get_current_view_name()
        if view_name == '原始图像':
            return self.context.source_image
        elif view_name == '遮罩':
            return self.context.mask_image
        elif view_name == '最终结果':
            return self.context.display_image
        else:
            return self.context.source_image

    def get_color_info_at(self, image_x: int, image_y: int) -> dict | None:
        """
        获取原始图片上某个坐标点的颜色信息
        """
        if self.context is None or self.context.source_image is None:
            return None

        image_height, image_width, _ = self.context.source_image.shape
        if not (0 <= image_y < image_height and 0 <= image_x < image_width):
            return None

        rgb_color = self.context.source_image[image_y, image_x]
        hsv_color = cv2.cvtColor(rgb_color.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]

        return {
            'pos': (image_x, image_y),
            'rgb': (int(rgb_color[0]), int(rgb_color[1]), int(rgb_color[2])),
            'hsv': (int(hsv_color[0]), int(hsv_color[1]), int(hsv_color[2]))
        }

    def get_pipeline_code(self) -> str:
        """
        生成整个流水线的代码
        """
        return CvCodeGenerator.generate_code(self.pipeline.steps)

    # ==================== 流水线文件操作(委托给CvService) ====================

    def get_pipeline_names(self) -> List[str]:
        return self.cv_service.get_pipeline_names()

    def save_pipeline(self, name: str) -> bool:
        if self.cv_service.save_pipeline(name, self.pipeline):
            self.active_pipeline_name = name
            return True
        return False

    def load_pipeline(self, name: str) -> bool:
        pipeline = self.cv_service.load_pipeline(name)
        if pipeline is not None:
            self.pipeline = pipeline
            self.active_pipeline_name = name
            return True
        return False

    def delete_pipeline(self, name: str):
        self.cv_service.delete_pipeline(name)
        if self.active_pipeline_name == name:
            self.active_pipeline_name = None
            self.pipeline = CvPipeline()

    def rename_pipeline(self, old_name: str, new_name: str):
        self.cv_service.rename_pipeline(old_name, new_name)
        if self.active_pipeline_name == old_name:
            self.active_pipeline_name = new_name

    # ==================== 模板文件操作(委托给CvService) ====================

    def get_screen_names(self) -> List[str]:
        """
        获取所有画面的名称，用于UI下拉框
        """
        return list(self.ctx.screen_loader.screen_info_map.keys())

    def get_area_names_by_screen(self, screen_name: str) -> List[str]:
        """
        根据画面名称，获取其下所有区域的名称
        """
        screen = self.ctx.screen_loader.get_screen(screen_name)
        if screen is None:
            return []
        return [area.area_name for area in screen.area_list]

    def get_template_names(self) -> List[str]:
        return self.cv_service.get_template_names()

    def get_template_info_list(self) -> List[TemplateInfo]:
        """
        获取所有模板的信息
        """
        return self.ctx.template_loader.get_all_template_info_from_disk(need_raw=True, need_config=True)

    def save_contour_as_template(self, template_name: str, contour_index: int) -> bool:
        """
        将当前上下文中的某个轮廓保存为模板
        """
        if self.context is None or not self.context.contours or not (0 <= contour_index < len(self.context.contours)):
            return False

        contour_to_save = self.context.contours[contour_index]
        return self.cv_service.save_template_contour(template_name, contour_to_save)

    def load_template_contour(self, template_name: str) -> np.ndarray:
        return self.cv_service.load_template_contour(template_name)

    def delete_template(self, template_name: str):
        self.cv_service.delete_template_contour(template_name)

    def rename_template(self, old_name: str, new_name: str):
        self.cv_service.rename_template_contour(old_name, new_name)