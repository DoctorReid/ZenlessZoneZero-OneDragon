from concurrent.futures import ThreadPoolExecutor

from one_dragon.custom.custom_config import CustomConfig
from one_dragon.utils import thread_utils

ONE_DRAGON_CONTEXT_EXECUTOR = ThreadPoolExecutor(thread_name_prefix='one_dragon_context', max_workers=1)


class OneDragonCustomContext:

    def __init__(self):
        self.custom_config: CustomConfig = CustomConfig()

    def init_by_config(self) -> None:
        pass