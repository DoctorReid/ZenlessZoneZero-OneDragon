from typing import Optional


class HollowLevelInfo:

    def __init__(self,
                 mission_type_name: Optional[str] = None,
                 mission_name: Optional[str] = None,
                 level: Optional[int] = None,
                 phase: Optional[int] = None,
                 ):
        self.mission_type_name: str = mission_type_name
        self.mission_name: str = mission_name
        self.level: int = level
        self.phase: int = phase

    def is_mission_type(self, mission_type_name: str, level: int) -> bool:
        return (self.mission_type_name is not None
                and self.mission_type_name == mission_type_name
                and self.level is not None
                and self.level == level)
