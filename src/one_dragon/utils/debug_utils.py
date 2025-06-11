import os
import time
from functools import lru_cache
from typing import Optional

import cv2
from cv2.typing import MatLike
import win32clipboard # 导入 pywin32 的剪贴板模块
import win32con
from PIL import Image # 导入 PIL 库，用于图片处理
import io # 导入 io 模块，用于处理字节流

from one_dragon.utils import os_utils, cv2_utils
from one_dragon.utils.log_utils import log


@lru_cache
def get_debug_dir_path() -> str:
    return os_utils.get_path_under_work_dir('.debug')


@lru_cache()
def get_debug_image_dir_path() -> str:
    return os_utils.get_path_under_work_dir('.debug', 'images')


def get_debug_image_path(filename, suffix: str = '.png') -> str:
    return os.path.join(get_debug_image_dir_path(), filename + suffix)


def get_debug_image(filename, suffix: str = '.png') -> MatLike:
    return cv2_utils.read_image(get_debug_image_path(filename, suffix))


def save_debug_image(image, file_name: Optional[str] = None, prefix: str = '') -> str:
    if file_name is None:
        file_name = '%s_%d' % (prefix, round(time.time() * 1000))
    path = get_debug_image_path(file_name)
    log.debug('临时图片保存 %s', path)
    
    bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, bgr_image)
    
    # --- 复制图片到剪贴板 ---
    try:
        # 将 BGR 格式的 OpenCV 图片转换为 RGB 格式的 PIL Image
        # 这是因为 win32clipboard 通常需要 DIB (Device Independent Bitmap) 格式的数据，
        # 而 PIL 可以很方便地将图片保存为 BMP 格式的字节流，其中包含 DIB 数据。
        pil_image = Image.fromarray(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB))
        output = io.BytesIO()
        pil_image.save(output, "BMP") 
        data = output.getvalue()[14:] 

        win32clipboard.OpenClipboard() 
        win32clipboard.EmptyClipboard() 
        win32clipboard.SetClipboardData(win32con.CF_DIB, data) # 设置剪贴板数据为 DIB 格式
        win32clipboard.CloseClipboard() 
        log.debug('图片已复制到剪贴板')
    except Exception as e:
        log.error('无法将图片复制到剪贴板: %s', e)

    return file_name