import os
import sys
import datetime
from functools import lru_cache


def join_create_dir(path: str, *subs) -> str:
    """
    拼接目录路径并创建不存在的目录
    :param path: 基础路径
    :param subs: 子目录路径
    :return: 拼接后的目录路径
    """
    target_path = path
    for sub in subs:
        if sub:
            target_path = os.path.join(target_path, sub)
            os.makedirs(target_path, exist_ok=True)
    return target_path


def get_path_in_project(*sub_paths: str) -> str:
    """
    获取当前工作目录下的子目录路径，并确保该路径存在
    :param sub_paths: 子目录路径
    :return: 拼接后的子目录路径
    """
    return join_create_dir(get_project_root(), *sub_paths)


@lru_cache
def is_exe() -> bool:
    """
    判断程序是否在 EXE 中运行
    :return: 是否在 EXE 中运行
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


@lru_cache
def get_project_root() -> str:
    """
    获取项目的根目录
    :return: 项目根目录路径
    """
    if is_exe():
        return os.path.dirname(sys.executable)
    project_dir = os.path.abspath(__file__)
    for _ in range(4):
        project_dir = os.path.dirname(project_dir)
    return project_dir


def get_env_variable(key: str) -> str:
    """
    获取环境变量的值
    :param key: 环境变量名
    :return: 环境变量值
    """
    return os.environ.get(key)


def get_env_or_default(key: str, default: str) -> str:
    """
    获取环境变量的值，若获取失败则返回默认值
    :param key: 环境变量名
    :param default: 默认值
    :return: 环境变量值或默认值
    """
    return get_env_variable(key) or default


def current_timestamp() -> str:
    """
    获取当前时间的字符串表示
    :return: 格式化的时间字符串 (yyyyMMddHHmmss)
    """
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def get_current_date(utc_offset: int = None) -> str:
    """
    获取当前日期的字符串表示（可以指定 UTC 偏移）
    :param utc_offset: UTC 偏移量
    :return: 格式化的日期字符串 (yyyyMMdd)
    """
    tz = datetime.timezone(datetime.timedelta(hours=utc_offset)) if utc_offset else None
    return datetime.datetime.now(tz=tz).strftime("%Y%m%d")


def adjust_date(date_str: str, day_offset: int = 0) -> str:
    """
    根据日期和偏移量计算新的日期
    :param date_str: 日期字符串 (yyyyMMdd)
    :param day_offset: 偏移的天数
    :return: 调整后的日期字符串 (yyyyMMdd)
    """
    date = datetime.datetime.strptime(date_str, "%Y%m%d") + datetime.timedelta(days=day_offset)
    return date.strftime("%Y%m%d")


def get_sunday(date_str: str) -> str:
    """
    获取指定日期所在周的星期天日期
    :param date_str: 日期字符串 (yyyyMMdd)
    :return: 星期天日期字符串 (yyyyMMdd)
    """
    date = datetime.datetime.strptime(date_str, "%Y%m%d")
    days_to_sunday = 6 - date.weekday()
    sunday_date = date + datetime.timedelta(days=days_to_sunday)
    return sunday_date.strftime("%Y%m%d")


def get_monday(date_str: str) -> str:
    """
    获取指定日期所在周的星期一日期
    :param date_str: 日期字符串 (yyyyMMdd)
    :return: 星期一日期字符串 (yyyyMMdd)
    """
    date = datetime.datetime.strptime(date_str, "%Y%m%d")
    days_to_monday = -date.weekday()
    monday_date = date + datetime.timedelta(days=days_to_monday)
    return monday_date.strftime("%Y%m%d")


def is_monday(date_str: str) -> bool:
    """
    判断指定日期是否为星期一
    :param date_str: 日期字符串 (yyyyMMdd)
    :return: 是否为星期一
    """
    return datetime.datetime.strptime(date_str, "%Y%m%d").weekday() == 0


def get_day_of_week(utc_offset: int = None) -> int:
    """
    获取当前日期的星期几 (1~7)
    :param utc_offset: UTC 偏移量
    :return: 星期几 (1=星期一, 7=星期天)
    """
    return (datetime.datetime.strptime(get_current_date(utc_offset), "%Y%m%d").weekday() + 1)


def date_diff(date1_str: str, date2_str: str) -> int:
    """
    计算两个日期之间相差的天数
    :param date1_str: 日期1字符串 (yyyyMMdd)
    :param date2_str: 日期2字符串 (yyyyMMdd)
    :return: 相差的天数
    """
    date1 = datetime.datetime.strptime(date1_str, "%Y%m%d")
    date2 = datetime.datetime.strptime(date2_str, "%Y%m%d")
    return (date1 - date2).days


def clean_old_debug_files(days: int = 1):
    """
    清理过期的调试文件
    :param days: 文件过期的天数
    """
    debug_dir = get_path_in_project('.debug')
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)

    for root, _, files in os.walk(debug_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff:
                os.remove(file_path)
