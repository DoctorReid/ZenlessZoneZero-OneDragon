from concurrent.futures import Future

from one_dragon.utils.log_utils import log


def handle_future_result(future: Future):
    try:
        future.result()
    except Exception:
        log.error('异步执行失败', exc_info=True)
