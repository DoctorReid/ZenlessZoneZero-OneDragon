import base64
import os
from typing import Union, List, Optional, Tuple

import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.matcher.match_result import MatchResultList, MatchResult

feature_detector = cv2.SIFT_create()


def read_image(file_path: str) -> Optional[MatLike]:
    """
    读取图片
    :param file_path: 图片路径
    :return:
    """
    if not os.path.exists(file_path):
        return None
    image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if image.ndim == 2:
        return image
    elif image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    elif image.ndim == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    else:
        return image


def save_image(img: MatLike, file_path: str) -> None:
    """
    保存图片
    :param img: RBG格式的图片
    :param file_path: 保存路径
    """
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(file_path, img)


def show_image(img: MatLike,
               rects: Union[MatchResult, MatchResultList] = None,
               win_name: str = 'DEBUG', wait: Optional[int] = None, destroy_after: bool = False):
    """
    显示一张图片
    :param img: 图片
    :param rects: 需要画出来的框
    :param win_name:
    :param wait: 显示后等待按键的秒数
    :param destroy_after: 显示后销毁窗口
    :return:
    """
    to_show = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if rects is not None:
        if type(rects) == MatchResult:
            cv2.rectangle(to_show, (rects.x, rects.y), (rects.x + rects.w, rects.y + rects.h), (255, 0, 0), 1)
        elif type(rects) == MatchResultList:
            for i in rects:
                cv2.rectangle(to_show, (i.x, i.y), (i.x + i.w, i.y + i.h), (255, 0, 0), 1)

    cv2.imshow(win_name, to_show)
    if wait is not None:
        cv2.waitKey(wait)
    if destroy_after:
        cv2.destroyWindow(win_name)


def image_rotate(img: MatLike, angle: float, show_result: bool = False):
    """
    对图片按中心进行旋转
    :param img: 原图
    :param angle: 逆时针旋转的角度
    :param show_result: 显示结果
    :return: 旋转后图片
    """
    height, width = img.shape[:2]
    center = (width // 2, height // 2)

    # 获取旋转矩阵
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # 应用旋转矩阵来旋转图像
    rotated_image = cv2.warpAffine(img, rotation_matrix, (width, height))

    if show_result:
        cv2.imshow('Result', rotated_image)

    return rotated_image


def mark_area_as_color(image: MatLike, pos: List, color, new_image: bool = False):
    """
    将图片的一个区域变颜色 然后返回新的图片
    :param image: 原图
    :param pos: 区域坐标 如果是矩形 传入 [x,y,w,h] 如果是圆形 传入 [x,y,r]。其他数组长度不处理
    :param new_image: 是否返回一张新的图
    :param color: 颜色
    :return: 新图
    """
    to_paint = image.copy() if new_image else image
    if not type(pos) is np.ndarray:
        pos = np.array([pos])
    for p in pos:
        if len(p) == 4:
            x, y, w, h = p[0], p[1], p[2], p[3]
            cv2.rectangle(to_paint, pt1=(x, y), pt2=(x + w, y + h), color=color, thickness=-1)
        if len(p) == 3:
            x, y, r = p[0], p[1], p[2]
            cv2.circle(to_paint, (x, y), r, color, -1)
    return to_paint


def match_template(source: MatLike, template: MatLike, threshold,
                   mask: np.ndarray = None, only_best: bool = True,
                   ignore_inf: bool = False) -> MatchResultList:
    """
    在原图中匹配模板 注意无法从负偏移量开始匹配 即需要保证目标模板不会在原图边缘位置导致匹配不到
    :param source: 原图
    :param template: 模板
    :param threshold: 阈值
    :param mask: 掩码
    :param only_best: 只返回最好的结果
    :param ignore_inf: 是否忽略无限大的结果
    :return: 所有匹配结果
    """
    tx, ty = template.shape[1], template.shape[0]
    # 进行模板匹配
    # show_image(source, win_name='source')
    # show_image(template, win_name='template')
    # show_image(mask, win_name='mask')
    result = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)

    match_result_list = MatchResultList(only_best=only_best)
    filtered_locations = np.where(np.logical_and(
        result >= threshold,
        np.isfinite(result) if ignore_inf else np.ones_like(result))
    )  # 过滤低置信度的匹配结果

    # 遍历所有匹配结果，并输出位置和置信度
    for pt in zip(*filtered_locations[::-1]):
        confidence = result[pt[1], pt[0]]  # 获取置信度
        match_result_list.append(MatchResult(confidence, pt[0], pt[1], tx, ty))

    return match_result_list


def concat_vertically(img: MatLike, next_img: MatLike, decision_height: int = 150):
    """
    垂直拼接图片。
    假设两张图片是通过垂直滚动得到的，即宽度一样，部分内容重叠
    :param img: 图
    :param next_img: 下一张图
    :param decision_height: 用第二张图的多少高度来判断重叠部分
    :return:
    """
    # 截取一个横截面用来匹配 要用中心部分 四周空白较多容易误判
    for threshold in range(95, 70, -5):
        for dh in range(decision_height, next_img.shape[0] // 2, 10):
            cy = next_img.shape[0] // 2
            next_part = next_img[:-dh, :]
            r = match_template(img, next_part, threshold / 100.0).max
            if r is None:
                continue
            h, w, _ = img.shape
            overlap_h = h - r.y
            extra_part = next_img[overlap_h+1:, :]
            # 垂直拼接两张图像
            return cv2.vconcat([img, extra_part])
    raise Exception('拼接图片失败')


def concat_horizontally(img: MatLike, next_img: MatLike, decision_width: int = 200):
    """
    水平拼接图片。
    假设两张图片是通过水平滚动得到的，即高度一样，部分内容重叠
    :param img: 图
    :param next_img: 下一张图
    :param decision_width: 用第二张图的多少宽度来判断重叠部分
    :return:
    """
    # 截取一个横截面用来匹配 要用中心部分 四周空白较多容易误判
    cx = next_img.shape[1] // 2
    next_part = next_img[:, cx - decision_width:cx + decision_width]
    result = match_template(img, next_part, 0.8)
    # 找出置信度最高的结果
    r = result.max
    h, w, _ = img.shape
    overlap_w = w - r.x + cx - decision_width
    extra_part = next_img[:, overlap_w+1:]
    # 水平拼接两张图像
    return cv2.hconcat([img, extra_part])


def concat_horizontally_2(img: MatLike, next_img: MatLike, decision_width: int = 200) -> MatLike:
    """
    水平拼接图片。 两张图片可能高度有一点差异，宽度应该是一样的
    :param img: 图
    :param next_img: 下一张图
    :param decision_width: 用第二张图的多少宽度来判断重叠部分
    :return:
    """
    if img.shape == next_img.shape:  # 大小一致时 使用旧的方法
        return concat_horizontally(img, next_img, decision_width)

    part_1 = img[50:-50, decision_width:]  # 上下剪掉一点 左边剪掉一点
    result = match_template(next_img, part_1, 0.8).max

    if result is None:
        return None

    height_1 = result.y + part_1.shape[0] + 50
    width_1 = result

    # 截取一个横截面用来匹配 要用中心部分 四周空白较多容易误判
    cx = next_img.shape[1] // 2
    next_part = next_img[:, cx - decision_width:cx + decision_width]

    # 找出置信度最高的结果
    r = result.max
    h, w, _ = img.shape
    overlap_w = w - r.x + cx - decision_width
    extra_part = next_img[:, overlap_w+1:]
    # 水平拼接两张图像
    return cv2.hconcat([img, extra_part])


def is_same_image(i1: MatLike, i2: MatLike, threshold: float = 1) -> bool:
    """
    简单使用均方差判断两图是否一致
    :param i1: 图1
    :param i2: 图2
    :param threshold: 低于阈值认为是相等
    :return: 是否同一张图
    """
    if i1.shape != i2.shape:
        return False
    return np.mean((i1 - i2) ** 2) < threshold


def color_similarity_2d(image, color):
    """
    PhotoShop 魔棒功能的容差是一样的，颜色差值 = abs(max(RGB差值)) + abs(min(RGB差值))
    感谢 https://github.com/LmeSzinc/StarRailCopilot/wiki/MinimapTracking
    :param image:
    :param color:
    :return:
    """
    b, g, r = cv2.split(cv2.subtract(image, (*color, 0)))
    positive = cv2.max(cv2.max(r, g), b)
    b, g, r = cv2.split(cv2.subtract((*color, 0), image))
    negative = cv2.max(cv2.max(r, g), b)
    return cv2.subtract(255, cv2.add(positive, negative))


def show_overlap(source, template, x, y, template_scale: float = 1, win_name: str = 'DEBUG', wait: int = 1):
    to_show_source = source.copy()

    if template_scale != 1:
        # 缩放后的宽度和高度
        scaled_width = int(template.shape[1] * template_scale)
        scaled_height = int(template.shape[0] * template_scale)

        # 缩放小图
        to_show_template = cv2.resize(template, (scaled_width, scaled_height))
    else:
        to_show_template = template

    source_overlap_template(to_show_source, to_show_template, x, y)
    show_image(to_show_source, win_name=win_name, wait=wait)


def feature_detect_and_compute(img: MatLike, mask: Optional[MatLike] = None):
    return feature_detector.detectAndCompute(img, mask=mask)


def feature_keypoints_to_np(keypoints):
    return np.array([(kp.pt[0], kp.pt[1], kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in keypoints])


def feature_keypoints_from_np(np_arr):
    return np.array([cv2.KeyPoint(x=kp[0], y=kp[1], size=kp[2], angle=kp[3],
                                  response=kp[4], octave=int(kp[5]), class_id=int(kp[6])) for kp in np_arr])


def feature_match(source_kp, source_desc, template_kp, template_desc,
                  source_mask: Optional[MatLike] = None):
    if len(source_kp) == 0 or len(template_kp) == 0:
        return None, None, None, None

    # feature_matcher = cv2.FlannBasedMatcher()
    feature_matcher = cv2.BFMatcher()
    matches = feature_matcher.knnMatch(template_desc, source_desc, k=2)
    # 应用比值测试，筛选匹配点
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:  # 不足4个优秀匹配点时 不能使用RANSAC
        return good_matches, None, None, None

    # 提取匹配点的坐标
    template_points = np.float32([template_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 模板的
    source_points = np.float32([source_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 原图的

    # 使用RANSAC算法估计模板位置和尺度
    _, mask = cv2.findHomography(template_points, source_points, cv2.RANSAC, 5.0, mask=source_mask)
    # 获取内点的索引 拿最高置信度的
    inlier_indices = np.where(mask.ravel() == 1)[0]
    if len(inlier_indices) == 0:  # mask 里没找到就算了 再用good_matches的结果也是很不准的
        return good_matches, None, None, None

    # 距离最短 置信度最高的结果
    best_match = None
    for i in range(len(good_matches)):
        if mask[i] == 1 and (best_match is None or good_matches[i].distance < best_match.distance):
            best_match = good_matches[i]

    query_point = source_kp[best_match.trainIdx].pt  # 原图中的关键点坐标 (x, y)
    train_point = template_kp[best_match.queryIdx].pt  # 模板中的关键点坐标 (x, y)

    # 获取最佳匹配的特征点的缩放比例
    query_scale = source_kp[best_match.trainIdx].size
    train_scale = template_kp[best_match.queryIdx].size
    template_scale = query_scale / train_scale

    # 模板图缩放后在原图上的偏移量
    offset_x = query_point[0] - train_point[0] * template_scale
    offset_y = query_point[1] - train_point[1] * template_scale

    return good_matches, offset_x, offset_y, template_scale


def feature_match_for_one(source_kp, source_desc, template_kp, template_desc,
                          template_width: int, template_height: int,
                          source_mask: Optional[MatLike] = None,
                          knn_distance_percent: float = 0.7) -> Optional[MatchResult]:
    """
    使用特征匹配找到一个匹配结果
    :param source_kp: 源图关键点
    :param source_desc: 源图描述子
    :param template_kp: 目标关键点
    :param template_desc: 目标描述子
    :param template_width: 目标原宽度
    :param template_height: 目标原高度
    :param source_mask: 源图掩码
    :param knn_distance_percent: 越小要求匹配程度越高
    :return: 缩放后的位置和大小
    """
    if len(source_kp) == 0 or len(template_kp) == 0:
        return None

    # feature_matcher = cv2.FlannBasedMatcher()
    feature_matcher = cv2.BFMatcher()
    matches = feature_matcher.knnMatch(template_desc, source_desc, k=2)
    # 应用比值测试，筛选匹配点
    good_matches = []
    for t in matches:
        if len(t) < 2:  # 没有match的情况
            return None
        m, n = t
        if m.distance < knn_distance_percent * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:  # 不足4个优秀匹配点时 不能使用RANSAC
        return None

    # 提取匹配点的坐标
    template_points = np.float32([template_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 模板的
    source_points = np.float32([source_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 原图的

    # 使用RANSAC算法估计模板位置和尺度
    _, mask = cv2.findHomography(template_points, source_points, cv2.RANSAC, 5.0, mask=source_mask)
    # 获取内点的索引 拿最高置信度的
    inlier_indices = np.where(mask.ravel() == 1)[0]
    if len(inlier_indices) == 0:  # mask 里没找到就算了 再用good_matches的结果也是很不准的
        return None

    # 距离最短 置信度最高的结果
    best_match = None
    for i in range(len(good_matches)):
        if mask[i] == 1 and (best_match is None or good_matches[i].distance < best_match.distance):
            best_match = good_matches[i]

    query_point = source_kp[best_match.trainIdx].pt  # 原图中的关键点坐标 (x, y)
    train_point = template_kp[best_match.queryIdx].pt  # 模板中的关键点坐标 (x, y)

    # 获取最佳匹配的特征点的缩放比例
    query_scale = source_kp[best_match.trainIdx].size
    train_scale = template_kp[best_match.queryIdx].size
    template_scale = query_scale / train_scale

    # 模板图缩放后在原图上的偏移量
    offset_x = query_point[0] - train_point[0] * template_scale
    offset_y = query_point[1] - train_point[1] * template_scale

    scaled_width = int(template_width * template_scale)
    scaled_height = int(template_height * template_scale)

    return MatchResult(1, offset_x, offset_y, scaled_width, scaled_height, template_scale)


def feature_match_for_multi(
        source_kp, source_desc, template_kp, template_desc,
        template_width: int, template_height: int,
        source_mask: Optional[MatLike] = None,
        knn_distance_percent: float = 0.7) -> MatchResultList:
    """

    :param source_kp:
    :param source_desc:
    :param template_kp:
    :param template_desc:
    :param template_width:
    :param template_height:
    :param source_mask:
    :param knn_distance_percent:
    :return:
    """
    match_result_list = MatchResultList(only_best=False)

    if len(source_kp) == 0 or len(template_kp) == 0:
        return match_result_list

    # feature_matcher = cv2.FlannBasedMatcher()
    feature_matcher = cv2.BFMatcher()
    matches = feature_matcher.knnMatch(template_desc, source_desc, k=3)
    # 应用比值测试，筛选匹配点
    good_matches = []
    for m, n, p in matches:
        if m.distance < knn_distance_percent * n.distance and m.distance < knn_distance_percent * p.distance:
            good_matches.append(m)

    if len(good_matches) < 4:  # 不足4个优秀匹配点时 不能使用RANSAC
        return match_result_list

    # 提取匹配点的坐标
    template_points = np.float32([template_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 模板的
    source_points = np.float32([source_kp[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # 原图的

    # 使用RANSAC算法估计模板位置和尺度
    M, mask = cv2.findHomography(template_points, source_points, cv2.RANSAC, 5.0, mask=source_mask)
    # 获取内点的索引 拿最高置信度的
    inlier_indices = np.where(mask.ravel() == 1)[0]
    if len(inlier_indices) == 0:  # mask 里没找到就算了 再用good_matches的结果也是很不准的
        return match_result_list

    for i in range(len(good_matches)):
        if mask[i] == 1:
            match = good_matches[i]

            query_point = source_kp[match.trainIdx].pt  # 原图中的关键点坐标 (x, y)
            train_point = template_kp[match.queryIdx].pt  # 模板中的关键点坐标 (x, y)

            # 获取最佳匹配的特征点的缩放比例
            query_scale = source_kp[match.trainIdx].size
            train_scale = template_kp[match.queryIdx].size
            template_scale = query_scale / train_scale

            # 模板图缩放后在原图上的偏移量
            offset_x = query_point[0] - train_point[0] * template_scale
            offset_y = query_point[1] - train_point[1] * template_scale

            # 缩放后的宽度和高度
            scaled_width = template_width * template_scale
            scaled_height = template_height * template_scale

            match_result_list.append(MatchResult(1, offset_x, offset_y, scaled_width, scaled_height))


    return match_result_list


def connection_erase(mask: MatLike, threshold: int = 50, erase_white: bool = True,
                     connectivity: int = 8) -> MatLike:
    """
    通过连通性检测 消除一些噪点
    :param mask: 黑白图 掩码图
    :param threshold: 小于多少连通时 认为是噪点
    :param erase_white: 是否清除白色
    :param connectivity: 连通性检测方向 4 or 8
    :return: 消除噪点后的图
    """
    to_check_connection = mask if erase_white else cv2.bitwise_not(mask)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(to_check_connection, connectivity=connectivity)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < threshold:
            large_components.append(label)

    result = mask.copy()
    for label in large_components:
        result[labels == label] = 0 if erase_white else 255

    return result


def crop_image(img, rect: Rect = None, copy: bool = False) -> Tuple[MatLike, Optional[Rect]]:
    """
    裁剪图片 裁剪区域可能超出图片范围
    :param img: 原图
    :param rect: 裁剪区域 (x1, y1, x2, y2)
    :param copy: 是否复制新图
    :return: 裁剪后图片 和 实际的裁剪区域
    """
    if rect is None:
        return (img.copy() if copy else img), None

    x1, y1, x2, y2 = rect.x1, rect.y1, rect.x2, rect.y2
    if x1 < 0:
        x1 = 0
    if x2 > img.shape[1]:
        x2 = img.shape[1]
    if y1 < 0:
        y1 = 0
    if y2 > img.shape[0]:
        y2 = img.shape[0]

    x1, y1 = int(x1), int(y1)
    x2, y2 = int(x2), int(y2)
    crop = img[y1: y2, x1: x2]
    return (crop.copy() if copy else crop), Rect(x1, y1, x2, y2)


def crop_image_only(img, rect: Rect = None, copy: bool = False) -> MatLike:
    """
    裁剪图片 裁剪区域可能超出图片范围
    :param img: 原图
    :param rect: 裁剪区域 (x1, y1, x2, y2)
    :param copy: 是否复制新图
    :return: 只返回裁剪后图片
    """
    return crop_image(img, rect=rect, copy=copy)[0]


def dilate(img, k):
    """
    膨胀一下 适合掩码图
    :param img:
    :param k:
    :return:
    """
    if k == 0:
        return img
    kernel = np.ones((k, k), np.uint8)
    return cv2.dilate(src=img, kernel=kernel, iterations=1)


def convert_to_standard(origin, mask, width: int = 51, height: int = 51, bg_color=None):
    """
    转化成 目标尺寸并居中
    :param origin:
    :param mask:
    :param width: 目标尺寸宽度
    :param height: 目标尺寸高度
    :param bg_color: 背景色
    :return:
    """
    final_mask = np.zeros((height, width), dtype=np.uint8)
    bw = np.where(mask == 255)
    if len(bw[0]) == 0:  # 遇袭情况下 有可能小地图上使用颜色扣图会完全扣不到 掩码全黑
        cx = mask.shape[1] // 2
        cy = mask.shape[0] // 2
        min_x, min_y = 0, 0
        max_x, max_y = mask.shape[1], mask.shape[0]
    else:
        white_pixel_coordinates = list(zip(bw[1], bw[0]))

        # 找到最大最小坐标值
        max_x = max(white_pixel_coordinates, key=lambda i: i[0])[0]
        max_y = max(white_pixel_coordinates, key=lambda i: i[1])[1]

        min_x = min(white_pixel_coordinates, key=lambda i: i[0])[0]
        min_y = min(white_pixel_coordinates, key=lambda i: i[1])[1]

        # 稍微扩大一下范围 why
        if max_x < mask.shape[1]:
            max_x += min(5, mask.shape[1] - max_x)
        if max_y < mask.shape[0]:
            max_y += min(5, mask.shape[0] - max_y)
        if min_x > 0:
            min_x -= min(5, min_x)
        if min_y > 0:
            min_y -= min(5, min_y)

        cx = (min_x + max_x) // 2
        cy = (min_y + max_y) // 2

    x1, y1 = cx - min_x, cy - min_y
    x2, y2 = max_x - cx, max_y - cy

    ccx = width // 2
    ccy = height // 2

    # 移动到 特定尺寸 居中
    final_mask[ccy-y1:ccy+y2, ccx-x1:ccx+x2] = mask[min_y:max_y, min_x:max_x]

    if len(origin.shape) > 2:
        final_origin = np.zeros((height, width, 3), dtype=np.uint8)
        final_origin[ccy-y1:ccy+y2, ccx-x1:ccx+x2, :] = origin[min_y:max_y, min_x:max_x, :]
    else:
        final_origin = np.zeros((height, width), dtype=np.uint8)
        final_origin[ccy - y1:ccy + y2, ccx - x1:ccx + x2] = origin[min_y:max_y, min_x:max_x]
    final_origin = cv2.bitwise_and(final_origin, final_origin, mask=final_mask)

    if bg_color is not None:  # 部分图标可以背景统一使用颜色
        final_origin[np.where(final_mask == 0)] = bg_color

    return final_origin, final_mask


def source_overlap_template(source, template, x, y, copy_img: bool = False):
    """
    在原图上覆盖模板图
    :param source: 原图
    :param template: 模板图 缩放后
    :param x: 偏移量
    :param y: 偏移量
    :param copy_img: 是否复制新图片
    :return:
    """
    to_overlap_source = source.copy() if copy_img else source

    rect1, rect2 = get_overlap_rect(source, template, x, y)
    sx_start, sy_start, sx_end, sy_end = rect1
    tx_start, ty_start, tx_end, ty_end = rect2

    # 将覆盖图像放置到底图的指定位置
    to_overlap_source[sy_start:sy_end, sx_start:sx_end] = template[ty_start:ty_end, tx_start:tx_end]

    return to_overlap_source


def get_overlap_rect(source, template, x, y):
    """
    根据模板图在原图上的偏移量 计算出覆盖区域
    :param source: 原图
    :param template: 模板图 缩放后
    :param x: 偏移量
    :param y: 偏移量
    :return:
    """
    # 获取要覆盖图像的宽度和高度
    overlay_height, overlay_width = template.shape[:2]

    # 覆盖图在原图上的坐标
    sx_start = int(x)
    sy_start = int(y)
    sx_end = sx_start + overlay_width
    sy_end = sy_start + overlay_height

    # 覆盖图要用的坐标
    tx_start = 0
    ty_start = 0
    tx_end = overlay_width
    ty_end = overlay_height

    # 覆盖图缩放后可以超出了原图的范围
    if sx_start < 0:
        tx_start -= sx_start
        sx_start -= sx_start
    if sx_end > source.shape[1]:
        tx_end -= sx_end - source.shape[1]
        sx_end -= sx_end - source.shape[1]

    if sy_start < 0:
        ty_start -= sy_start
        sy_start -= sy_start
    if sy_end > source.shape[0]:
        ty_end -= sy_end - source.shape[0]
        sy_end -= sy_end - source.shape[0]

    return (sx_start, sy_start, sx_end, sy_end), (tx_start, ty_start, tx_end, ty_end)


def get_four_corner(bw):
    """
    获取四个方向最远的白色像素点的位置
    :param bw: 黑白图
    :return:
    """
    white = np.where(bw == 255)
    if np.sum(bw == 255) == 0:
        return None, None, None, None
    left = (white[1][np.argmin(white[1])], white[0][np.argmin(white[1])])
    right = (white[1][np.argmax(white[1])], white[0][np.argmax(white[1])])
    top = (white[1][np.argmin(white[0])], white[0][np.argmin(white[0])])
    bottom = (white[1][np.argmax(white[0])], white[0][np.argmax(white[0])])
    return left, right, top, bottom


def scale_image(img: Optional[MatLike] = None, scale: Optional[float] = None, copy: bool = True) -> Optional[MatLike]:
    """
    按比例缩放图片
    :param img: 原图
    :param scale: 缩放比例
    :param copy: 是否复制新图
    :return: 缩放后图片
    """
    if img is None:
        return None
    if scale is None or scale == 1:
        return img.copy() if copy else img
    target_size = (int(img.shape[0] * scale), int(img.shape[1] * scale))
    return cv2.resize(img, target_size)


def to_base64(img: MatLike) -> str:
    """
    将图片转化成base64编码展示
    :param img:
    :return:
    """
    _, buffer = cv2.imencode('.png', img)
    base64_data = base64.b64encode(buffer)
    return base64_data.decode("utf-8")


def get_white_part(img: MatLike,
                   noise_threshold: Optional[int] = None):
    """
    获取白色的部分掩码
    :param img:
    :param noise_threshold: 噪音阈值。传入时会消除小于多少
    :return:
    """
    return color_in_range(img, lower=[220, 220, 220], upper=[255, 255, 255],
                          noise_threshold=noise_threshold)


def get_black_part(img: MatLike,
                   noise_threshold: Optional[int] = None):
    """
    获取白色的部分掩码
    :param img:
    :param noise_threshold: 噪音阈值。传入时会消除小于多少
    :return:
    """
    return color_in_range(img, lower=[0, 0, 0], upper=[50, 50, 50],
                          noise_threshold=noise_threshold)


def color_in_range(img: MatLike, lower: List[int], upper: List[int],
                   noise_threshold: Optional[int] = None):
    """
    获取颜色范围内的掩码
    :param img:
    :param lower: 颜色下限
    :param upper: 颜色上限
    :param noise_threshold: 噪音阈值。传入时会消除小于多少
    :return:
    """
    lower_color = np.array(lower, dtype=np.uint8)
    upper_color = np.array(upper, dtype=np.uint8)
    part = cv2.inRange(img, lower_color, upper_color)
    if noise_threshold is None:
        return part
    else:
        return connection_erase(part, noise_threshold)
