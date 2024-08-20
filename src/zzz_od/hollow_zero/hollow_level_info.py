from typing import Optional


class HollowLevelInfo:

    def __init__(self,
                 mission_type_name: Optional[str] = None,
                 mission_name: Optional[str] = None,
                 level: int = -1,
                 phase: int = -1,
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

    def to_next_level(self) -> None:
        if self.level == -1:
            return
        self.level += 1
        self.phase = 1

    def to_next_phase(self) -> None:
        if self.phase == -1:
            return
        self.phase += 1
