import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

class Banner(QWidget):
    """展示带有圆角的固定大小横幅小部件"""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.banner_image = self.load_banner_image(image_path)
        self.update_scaled_image()

    def load_banner_image(self, image_path: str):
        """加载横幅图片，或创建渐变备用图片"""
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
        self.scaled_image = self.banner_image.scaled(
            self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        self.update()

    def resizeEvent(self, event):
        """重载 resizeEvent 以更新缩放后的图片"""
        self.update_scaled_image()
        super().resizeEvent(event)

    def paintEvent(self, event):
        """重载 paintEvent 以绘制缩放后的图片"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        w, h = self.width(), self.height()
        path.addRoundedRect(0, 0, w, h, 20, 20)
        painter.setClipPath(path)

        # 计算绘制位置，以原图的右下角为顶点进行渲染
        source_w, source_h = self.scaled_image.width(), self.scaled_image.height()
        target_x = max(0, source_w - w)
        target_y = max(0, source_h - h)

        # 在窗口上绘制缩放后的图片
        painter.drawPixmap(0, 0, w, h, self.scaled_image, target_x, target_y, w, h)

    def set_percentage_size(self, width_percentage, height_percentage):
        """设置 Banner 的大小为窗口大小的百分比"""
        parent = self.parentWidget()
        if parent:
            new_width = int(parent.width() * width_percentage)
            new_height = int(parent.height() * height_percentage)
            self.setFixedSize(new_width, new_height)
            self.update_scaled_image()
