import logging
import os

_VERBOSE = str(os.getenv("OD_YOLO_VERBOSE", True)).lower() == "true"  # 开启日志


def get_logger():
    level = logging.INFO if _VERBOSE else logging.ERROR
    logger = logging.getLogger('OneDragon-YOLO')
    logger.handlers.clear()
    logger.setLevel(level)

    formatter = logging.Formatter('[%(asctime)s] [%(filename)s %(lineno)d] [%(levelname)s]: %(message)s', '%H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


log = get_logger()
