from typing import Optional


class LostVoidArtifact:

    def __init__(self, category: str, name: str, level: str, template_id: Optional[str] = None):
        self.category: str = category  # 分类
        self.name: str = name  # 名称
        self.level: str = level  # 等级
        self.template_id: str = template_id  # 模板ID 仅初始武备有