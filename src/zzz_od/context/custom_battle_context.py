import time
from concurrent.futures import ThreadPoolExecutor, Future

import threading
from cv2.typing import MatLike
from enum import Enum
from typing import Optional, List

from one_dragon.base.conditional_operation.state_event import StateEvent
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.utils import cv2_utils, debug_utils, thread_utils
from one_dragon.utils.log_utils import log
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.agent import Agent, AgentEnum


class CustomBattleEventEnum(Enum):

    CUSTOM_1 = '自定义状态-1'
    CUSTOM_2 = '自定义状态-1'
    CUSTOM_3 = '自定义状态-1'
    CUSTOM_4 = '自定义状态-1'
    CUSTOM_5 = '自定义状态-1'
    CUSTOM_6 = '自定义状态-1'
    CUSTOM_7 = '自定义状态-1'
    CUSTOM_8 = '自定义状态-1'
    CUSTOM_9 = '自定义状态-1'


class CustomBattleContext:

    def __init__(self, ctx: ZContext):
        self.ctx: ZContext = ctx