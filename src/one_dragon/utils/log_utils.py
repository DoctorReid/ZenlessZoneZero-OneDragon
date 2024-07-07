import logging
import os
from logging.handlers import TimedRotatingFileHandler

from one_dragon.utils import os_utils


def get_logger():
    logger = logging.getLogger('OneDragon')
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] [%(filename)s %(lineno)d] [%(levelname)s]: %(message)s', '%H:%M:%S')

    log_file_path = os.path.join(os_utils.get_path_under_work_dir('.log'), 'log.txt')
    archive_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=3, encoding='utf-8')
    archive_handler.setLevel(logging.INFO)
    archive_handler.setFormatter(formatter)
    logger.addHandler(archive_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def set_log_level(level: int) -> None:
    """
    显示日志等级
    :param level:
    :return:
    """
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)


log = get_logger()
