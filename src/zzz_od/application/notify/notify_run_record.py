from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord
from one_dragon.utils import cv2_utils, thread_utils, cal_utils, os_utils, yolo_config_utils
from zzz_od.application.notify.notify_config import NotifyConfig


class NotifyRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(self, 'notify', instance_idx=instance_idx,
                              game_refresh_hour_offset=game_refresh_hour_offset)
        


