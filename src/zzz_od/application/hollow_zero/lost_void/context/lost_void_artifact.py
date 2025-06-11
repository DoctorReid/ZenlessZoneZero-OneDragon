from typing import Optional


class LostVoidArtifact:

    def __init__(self, category: str, name: str, level: str,
                 is_gear: bool = False,
                 template_id: Optional[str] = None):
        self.category: str = category  # 分类
        self.name: str = name  # 名称
        self.level: str = level  # 等级
        self.is_gear: bool = is_gear  # 是否武备
        self.template_id: str = template_id  # 模板ID 仅部分武备有
        self.display_name: str = f'{self.category} {self.name}'
