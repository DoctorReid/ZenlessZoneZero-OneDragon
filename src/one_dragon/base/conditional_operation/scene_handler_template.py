from typing import Optional

from one_dragon.base.config.yaml_config import YamlConfig


class SceneHandlerTemplate(YamlConfig):

    def __init__(self, sub_dir: str, template_id: str, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name=template_id,
            sub_dir=[sub_dir],
            instance_idx=instance_idx,
            sample=True
        )

        self.template_name: str = self.get('template_name', '')
