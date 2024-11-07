import os
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget
from ...utils.file_utils import get_path_in_project,join_create_dir

class Banner(QWidget):
    """展示带有圆角的固定大小横幅小部件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(650)
        self.setFixedWidth(870)
        self.banner_image = self.load_banner_image()
        self.update_scaled_image()

    def load_banner_image(self):
        """加载横幅图片，或创建渐变备用图片"""
        image_path = os.path.join(
            join_create_dir(get_path_in_project(),'assets',"ui"), "1.png"
        )
        if os.path.isfile(image_path):
            return QPixmap(image_path)
        return self._create_fallback_image()

    def _create_fallback_image(self):
        """创建渐变备用图片"""
        fallback_image = QPixmap(2560, 1280)  # 使用原始图片的大小
        fallback_image.fill(Qt.gray)
        return fallback_image

    def update_scaled_image(self):
        """按高度缩放图片，宽度保持比例，超出裁剪"""
        original_width = self.banner_image.width()
        original_height = self.banner_image.height()

        # 获取设备像素比
        pixel_ratio = self.devicePixelRatio()

        # 根据高度计算宽度
        height_ratio = self.height() / original_height
        new_width = int(original_width * height_ratio)

        # 使用设备像素比进行缩放，避免模糊
        size = QSize(new_width, self.height())
        self.scaled_image = self.banner_image.scaled(
            size * pixel_ratio,  # 使用设备像素比来缩放
            Qt.IgnoreAspectRatio,  # 忽略宽高比，强制缩放
            Qt.SmoothTransformation,
        )

        # 设置设备像素比，确保图像在高分辨率设备上显示正确
        self.scaled_image.setDevicePixelRatio(pixel_ratio)

    def paintEvent(self, event):
        """重载 paintEvent 以绘制缩放后的图片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.addRoundedRect(0, 0, w, h, 20, 20)
        painter.setClipPath(path)

        # 在窗口上绘制缩放后的图片
        painter.drawPixmap(-80, 0, self.scaled_image)
