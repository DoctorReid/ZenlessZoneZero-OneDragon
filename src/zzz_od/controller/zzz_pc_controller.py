from one_dragon.base.controller.pc_controller_base import PcControllerBase


class PcController(PcControllerBase):

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        PcControllerBase.__init__(self,
                                  win_title=win_title,
                                  standard_width=standard_width,
                                  standard_height=standard_height)
